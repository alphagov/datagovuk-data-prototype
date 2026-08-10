#!/usr/bin/env python3
"""
Restore CKAN database from S3 backup to RDS.

This script:
1. Lists available backups in S3
2. Downloads the latest (or specified) backup
3. Decompresses it
4. Restores into RDS using pg_restore
5. Runs any necessary migrations

Requires:
- AWS credentials with S3 read access and RDS connect permission
- PostgreSQL client tools (pg_restore, psql)
- Python 3.9+
"""

import argparse
import gzip
import io
import json
import logging
import os
import subprocess
import sys
import tempfile

import boto3
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CKANDatabaseRestorer:
    def __init__(
        self,
        s3_bucket: str,
        rds_endpoint: str,
        db_name: str,
        db_user: str = "dbadmin",
        aws_region: str = "eu-west-2",
        s3_prefix: str = "",
    ):
        """Initialize the restorer with AWS and RDS credentials."""
        self.s3_bucket = s3_bucket
        self.rds_endpoint = rds_endpoint
        self.db_name = db_name
        self.db_user = db_user
        self.aws_region = aws_region
        self.s3_prefix = s3_prefix.rstrip('/') if s3_prefix else ""
        
        # Extract hostname from endpoint (remove port if present)
        self.rds_host = rds_endpoint.split(':')[0]
        self.rds_port = 5432
        
        self.s3_client = boto3.client('s3', region_name=aws_region)
        self.rds_client = boto3.client('rds', region_name=aws_region)
        self.secrets_client = boto3.client('secretsmanager', region_name=aws_region)
        
    def list_backups(self) -> list:
        """List all available backups in S3."""
        logger.info(f"Listing backups in s3://{self.s3_bucket}/{self.s3_prefix}")
        
        prefix = f"{self.s3_prefix}/" if self.s3_prefix else ""
        response = self.s3_client.list_objects_v2(
            Bucket=self.s3_bucket,
            Prefix=prefix
        )
        
        backups = []
        if 'Contents' in response:
            for obj in response['Contents']:
                # Skip if it's a directory or prefix
                if not obj['Key'].endswith('/'):
                    backups.append({
                        'key': obj['Key'],
                        'size_gb': obj['Size'] / (1024**3),
                        'last_modified': obj['LastModified'],
                    })
        
        # Sort by last modified, newest first
        backups.sort(key=lambda x: x['last_modified'], reverse=True)
        return backups
    
    def download_backup(self, s3_key: str, local_path: Path) -> Path:
        """Download backup from S3."""
        logger.info(f"Downloading s3://{self.s3_bucket}/{s3_key}")
        logger.info(f"Destination: {local_path}")
        
        try:
            self.s3_client.download_file(
                self.s3_bucket,
                s3_key,
                str(local_path)
            )
            logger.info(f"Downloaded {local_path.stat().st_size / (1024**3):.2f} GB")
            return local_path
        except Exception as e:
            logger.error(f"Failed to download backup: {e}")
            raise
    
    def decompress_backup(self, compressed_path: Path, output_path: Path) -> Path:
        """Decompress gzipped backup file."""
        logger.info(f"Decompressing {compressed_path.name}")
        
        try:
            with gzip.open(compressed_path, 'rb') as f_in:
                with open(output_path, 'wb') as f_out:
                    f_out.writelines(f_in)
            logger.info(f"Decompressed to {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Failed to decompress backup: {e}")
            raise
    
    def get_rds_password(self) -> str:
        """Retrieve master password from RDS-managed Secrets Manager secret."""
        secret_arn = os.environ.get('RDS_SECRET_ARN')
        if not secret_arn:
            raise RuntimeError("RDS_SECRET_ARN environment variable is not set")
        logger.info(f"Retrieving RDS master password from {secret_arn}")
        try:
            value = self.secrets_client.get_secret_value(SecretId=secret_arn)
            secret = json.loads(value['SecretString'])
            return secret['password']
        except Exception as e:
            logger.error(f"Failed to retrieve RDS password: {e}")
            raise
    
    def restore_database_from_file(self, backup_path: Path) -> bool:
        """Restore database from a local backup file."""
        logger.info("Starting database restore from local file")
        logger.info(f"RDS endpoint: {self.rds_endpoint}")
        logger.info(f"Database: {self.db_name}")
        logger.info(f"User: {self.db_user}")
        logger.info(f"Backup file: {backup_path}")

        auth_token = self.get_rds_password()
        env = os.environ.copy()
        env['PGPASSWORD'] = auth_token
        env['PGSSLMODE'] = 'require'
        env['PGOPTIONS'] = (
            '-c statement_timeout=0'
            ' -c idle_in_transaction_session_timeout=0'
            ' -c tcp_keepalives_idle=30'
            ' -c tcp_keepalives_interval=10'
            ' -c tcp_keepalives_count=10'
        )

        # Step 1: Drop and recreate the database
        logger.info("Step 1/2: Dropping existing database (if exists)")
        logger.info(f"Dropping existing database {self.db_name} (FORCE)")
        subprocess.run(
            ['psql', '-h', self.rds_host, '-U', self.db_user, '-d', 'postgres',
             '-c', f'DROP DATABASE IF EXISTS {self.db_name} WITH (FORCE);'],
            env=env, check=True, capture_output=True,
        )

        logger.info(f"Creating database {self.db_name}")
        subprocess.run(
            ['psql', '-h', self.rds_host, '-U', self.db_user, '-d', 'postgres',
             '-c', f'CREATE DATABASE {self.db_name};'],
            env=env, check=True, capture_output=False,
        )

        # Step 2: Restore from local file using pg_restore
        logger.info("Step 2/2: Restoring from local file (this may take 30-60 minutes)")

        pg_restore_proc = subprocess.Popen(
            [
                'pg_restore',
                '-h', self.rds_host,
                '-U', self.db_user,
                '-d', self.db_name,
                '--no-acl',
                '--no-owner',
                '--format=custom',
                '-v',
                str(backup_path),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
        )

        stdout, stderr = pg_restore_proc.communicate()
        returncode = pg_restore_proc.returncode

        if stdout:
            logger.info(f"pg_restore stdout:\n{stdout.decode('utf-8', errors='replace')}")
        if stderr:
            logger.warning(f"pg_restore stderr:\n{stderr.decode('utf-8', errors='replace')}")

        if returncode not in (0, 1):
            raise subprocess.CalledProcessError(returncode, 'pg_restore')

        logger.info("Database restore completed successfully")
        return True

    def restore_database_streaming(self, s3_key: str) -> bool:
        """Restore database by streaming directly from S3 — no local disk writes.

        DEPRECATED: Use restore_database_from_file() instead. Streaming causes
        broken pipe errors on large backups (>5GB) due to back-pressure during
        pg_restore's index building phase. Download-first approach is more reliable.
        """
        logger.warning("Using deprecated streaming restore. Consider using restore_database_from_file() instead.")
        logger.info("Starting streaming database restore (no local disk)")
        logger.info(f"RDS endpoint: {self.rds_endpoint}")
        logger.info(f"Database: {self.db_name}")
        logger.info(f"User: {self.db_user}")

        auth_token = self.get_rds_password()
        env = os.environ.copy()
        env['PGPASSWORD'] = auth_token
        env['PGSSLMODE'] = 'require'
        # Keepalives prevent NAT gateway from silently dropping idle TCP connections
        # during long-running statements (e.g. CREATE INDEX). Timeout disabled so
        # the full restore (potentially multi-hour) is never interrupted by RDS.
        # Aggressive keepalives: send every 30s, fail after 10 missed (5min total)
        env['PGOPTIONS'] = (
            '-c statement_timeout=0'
            ' -c idle_in_transaction_session_timeout=0'
            ' -c tcp_keepalives_idle=30'
            ' -c tcp_keepalives_interval=10'
            ' -c tcp_keepalives_count=10'
        )
        # Also set OS-level keepalive via socket options (if supported)
        env['PGKEEPALIVES'] = '1'
        env['PGKEEPALIVES_IDLE'] = '30'
        env['PGKEEPALIVES_INTERVAL'] = '10'
        env['PGKEEPALIVES_COUNT'] = '10'

        # Step 1: Drop and recreate the database
        logger.info("Step 1/2: Dropping existing database (if exists)")

        # Drop the database with FORCE to terminate any active connections (PG13+)
        logger.info(f"Dropping existing database {self.db_name} (FORCE)")
        subprocess.run(
            ['psql', '-h', self.rds_host, '-U', self.db_user, '-d', 'postgres',
             '-c', f'DROP DATABASE IF EXISTS {self.db_name} WITH (FORCE);'],
            env=env, check=True, capture_output=True,
        )

        logger.info(f"Creating database {self.db_name}")
        subprocess.run(
            ['psql', '-h', self.rds_host, '-U', self.db_user, '-d', 'postgres',
             '-c', f'CREATE DATABASE {self.db_name};'],
            env=env, check=True, capture_output=False,
        )

        # Step 2: Stream S3 → gunzip (if needed) → pg_restore stdin; no local file written
        logger.info("Step 2/2: Streaming restore (this may take 30-60 minutes)")
        logger.info(f"Source: s3://{self.s3_bucket}/{s3_key}")

        s3_obj = self.s3_client.get_object(Bucket=self.s3_bucket, Key=s3_key)

        # Peek at first bytes to detect format (gzip magic: 0x1f 0x8b)
        first_bytes = s3_obj['Body'].read(2)
        is_gzipped = first_bytes == b'\x1f\x8b'
        logger.info(f"Backup format: {'gzip-compressed' if is_gzipped else 'PostgreSQL custom binary'}")

        # Reconstruct stream with peek bytes prepended
        remaining_stream = io.BytesIO(first_bytes) if first_bytes else io.BytesIO()
        # Chain first bytes with rest of stream
        class ChainedStream:
            def __init__(self, prefix_bytes, s3_body):
                self.prefix = io.BytesIO(prefix_bytes)
                self.s3_body = s3_body
                self.reading_prefix = True

            def read(self, size=-1):
                if self.reading_prefix:
                    chunk = self.prefix.read(size)
                    if chunk:
                        return chunk
                    self.reading_prefix = False
                return self.s3_body.read(size)

        remaining_stream = ChainedStream(first_bytes, s3_obj['Body'])

        pg_restore_proc = subprocess.Popen(
            [
                'pg_restore',
                '-h', self.rds_host,
                '-U', self.db_user,
                '-d', self.db_name,
                '--no-acl',
                '--no-owner',
                '--format=custom',
                '-v',  # Verbose to see what's happening
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
        )

        try:
            # Use 8MB chunks for efficiency
            # Parallel pg_restore (--jobs=4) should prevent stalls
            chunk_size = 8 * 1024 * 1024
            bytes_streamed = 0

            if is_gzipped:
                # Decompress gzipped backup
                gunzip_proc = subprocess.Popen(
                    ['gunzip'],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    env=env,
                )

                # Feed stream to gunzip, read decompressed data, feed to pg_restore
                try:
                    for chunk in iter(lambda: remaining_stream.read(chunk_size), b''):
                        gunzip_proc.stdin.write(chunk)
                        bytes_streamed += len(chunk)
                        if bytes_streamed % (50 * 1024 * 1024) == 0:
                            logger.info(f"Streamed {bytes_streamed / (1024**3):.1f} GB to gunzip")
                except (BrokenPipeError, IOError) as e:
                    logger.error(f"S3 stream interrupted after {bytes_streamed / (1024**3):.1f} GB: {e}")
                    raise
                finally:
                    gunzip_proc.stdin.close()

                # Read decompressed data from gunzip and pipe to pg_restore
                while True:
                    chunk = gunzip_proc.stdout.read(chunk_size)
                    if not chunk:
                        break
                    pg_restore_proc.stdin.write(chunk)
                gunzip_proc.wait()
            else:
                # Stream raw PostgreSQL custom format directly to pg_restore
                try:
                    while True:
                        chunk = remaining_stream.read(chunk_size)
                        if not chunk:
                            break
                        pg_restore_proc.stdin.write(chunk)
                        bytes_streamed += len(chunk)
                        if bytes_streamed % (50 * 1024 * 1024) == 0:
                            logger.info(f"Streamed {bytes_streamed / (1024**3):.1f} GB from S3")
                except (BrokenPipeError, IOError) as e:
                    logger.error(f"S3 stream interrupted after {bytes_streamed / (1024**3):.1f} GB: {e}")
                    raise
        finally:
            pg_restore_proc.stdin.close()

        stdout, stderr = pg_restore_proc.communicate()
        returncode = pg_restore_proc.returncode

        # Log all pg_restore output for diagnostics
        if stdout:
            logger.info(f"pg_restore stdout:\n{stdout.decode('utf-8', errors='replace')}")
        if stderr:
            logger.warning(f"pg_restore stderr:\n{stderr.decode('utf-8', errors='replace')}")

        # Only fail on actual connection errors or OOM, not on parameter mismatches
        if returncode not in (0, 1):
            raise subprocess.CalledProcessError(returncode, 'pg_restore')

        logger.info("Streaming database restore completed successfully")
        return True


def main():
    parser = argparse.ArgumentParser(
        description="Restore CKAN database from S3 backup to RDS"
    )
    parser.add_argument(
        '--s3-bucket',
        default=os.environ.get('S3_BUCKET'),
        help='S3 bucket containing backups'
    )
    parser.add_argument(
        '--rds-endpoint',
        default=os.environ.get('RDS_ENDPOINT'),
        help='RDS endpoint (hostname:port)'
    )
    parser.add_argument(
        '--db-name',
        default='ckan',
        help='Database name (default: ckan)'
    )
    parser.add_argument(
        '--db-user',
        default='dbadmin',
        help='Database user (default: dbadmin)'
    )
    parser.add_argument(
        '--aws-region',
        default='eu-west-2',
        help='AWS region (default: eu-west-2)'
    )
    parser.add_argument(
        '--s3-prefix',
        default='',
        help='S3 prefix to search for backups (default: root)'
    )
    parser.add_argument(
        '--backup-s3-key',
        help='Specific S3 key to restore (if not provided, uses latest)'
    )
    parser.add_argument(
        '--list-only',
        action='store_true',
        help='Only list available backups and exit'
    )

    args = parser.parse_args()

    # Validate required parameters
    if not args.s3_bucket or not args.rds_endpoint:
        logger.error("Missing required parameters: --s3-bucket and --rds-endpoint (or S3_BUCKET and RDS_ENDPOINT env vars)")
        return 1

    try:
        restorer = CKANDatabaseRestorer(
            s3_bucket=args.s3_bucket,
            rds_endpoint=args.rds_endpoint,
            db_name=args.db_name,
            db_user=args.db_user,
            aws_region=args.aws_region,
            s3_prefix=args.s3_prefix,
        )
        
        # List available backups
        backups = restorer.list_backups()
        if not backups:
            logger.error("No backups found in S3")
            return 1
        
        logger.info(f"Found {len(backups)} backup(s)")
        for i, backup in enumerate(backups[:5]):  # Show top 5
            logger.info(f"  {i+1}. {backup['key']} ({backup['size_gb']:.2f} GB) - {backup['last_modified']}")
        
        if args.list_only:
            return 0
        
        # Choose which backup to restore
        if args.backup_s3_key:
            backup_key = args.backup_s3_key
        else:
            backup_key = backups[0]['key']  # Latest
        
        logger.info(f"Will restore: {backup_key}")

        # Download → decompress → restore from local file
        # This avoids broken pipe errors on large backups (streaming caused stalls at 5-67 minutes)
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Download from S3 (boto3 handles retries automatically)
            compressed_path = tmp_path / "ckan_backup.gz"
            restorer.download_backup(backup_key, compressed_path)

            # Decompress
            decompressed_path = tmp_path / "ckan_backup.dump"
            restorer.decompress_backup(compressed_path, decompressed_path)

            # Restore from local file (no streaming pressure)
            restorer.restore_database_from_file(decompressed_path)

        logger.info("Restore process completed successfully!")
        return 0
        
    except Exception as e:
        logger.error(f"Restore failed: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
