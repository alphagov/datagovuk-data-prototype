import csv
import httpx
import truststore
import ssl
import click

from pathlib import Path
from collections import defaultdict


FHRS_URL = "https://safhrsprodstorage.blob.core.windows.net/opendatafileblobstorage/FHRS_All_en-GB.csv"


def download_fhrs_data(file_path):
    if file_path.exists():
        click.echo(f"Using existing file: {file_path}")
        return

    click.echo(f"Downloading FHRS data from: {FHRS_URL}")
    file_path.parent.mkdir(parents=True, exist_ok=True)

    ctx = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    client = httpx.Client(verify=ctx, timeout=300.0)

    with client.stream("GET", FHRS_URL) as response:
        response.raise_for_status()
        with open(file_path, "wb") as f:
            for chunk in response.iter_bytes(chunk_size=8192):
                f.write(chunk)

    click.echo(f"Downloaded to: {file_path}")


def load_region_lookup(lookup_file):
    authority_to_region = {}

    with open(lookup_file) as f:
        reader = csv.DictReader(f)
        for row in reader:
            lad_name = row.get("local-authority-name", "")
            region_name = row.get("region", "")
            if lad_name and region_name:
                authority_to_region[lad_name] = region_name

    return authority_to_region


def aggregate_ratings(fhrs_file, authority_to_region):
    region_ratings = defaultdict(lambda: defaultdict(int))
    unmatched_authorities = set()
    total_records = 0
    matched_records = 0

    with open(fhrs_file, "r") as f:
        reader = csv.DictReader(f)

        for row in reader:
            total_records += 1
            authority_name = row.get("LocalAuthorityName", "")
            rating_value = row.get("RatingValue", "")

            if not authority_name or not rating_value:
                continue

            try:
                rating = int(rating_value)
                if rating < 1 or rating > 5:
                    continue
            except ValueError:
                continue

            if authority_name in authority_to_region:
                region = authority_to_region[authority_name]
                region_ratings[region][rating] += 1
                matched_records += 1
            else:
                unmatched_authorities.add(authority_name)

    return region_ratings, unmatched_authorities, total_records, matched_records


def save_to_csv(region_ratings, output_file):
    regions = sorted(region_ratings.keys())

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["region", "1", "2", "3", "4", "5", "total-number-of-establishments"]
        )

        for region in regions:
            ratings = region_ratings[region]
            row = [region]
            row_total = 0
            for rating in range(1, 6):
                count = ratings.get(rating, 0)
                row.append(count)
                row_total += count
            row.append(row_total)
            writer.writerow(row)


@click.command()
def aggregate():
    data_dir = Path(__file__).parent.parent / "data"
    reference_dir = data_dir / "reference"
    fhrs_file = reference_dir / "FHRS_All_en-GB.csv"
    lookup_file = reference_dir / "fhrs-local-authority-by-region.csv"

    download_fhrs_data(fhrs_file)

    click.echo("Reading FHRS region lookup")
    authority_to_region = load_region_lookup(lookup_file)
    click.echo(f"Loaded {len(authority_to_region):,} local authority mappings")

    click.echo("Reading and aggregating food hygiene data")
    region_ratings, unmatched, total_records, matched_records = aggregate_ratings(
        fhrs_file, authority_to_region
    )

    output_file = data_dir / "fhrs-ratings-by-region.csv"
    save_to_csv(region_ratings, output_file)
    click.echo(f"Results saved to: {output_file}")

    if len(unmatched) > 0:
        click.echo(f"There were {len(unmatched)} unmatched local authorities")
        unmatched_file = reference_dir / "fhrs-unmatched-local-authorities.csv"
        with open(unmatched_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["local-authority-name"])
            for authority in sorted(unmatched):
                writer.writerow([authority])
        click.echo(f"Unmatched authorities saved to: {unmatched_file}")
