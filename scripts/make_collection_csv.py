import subprocess
import tempfile
from pathlib import Path

import click
import frontmatter

from scripts.config import (
    COLLECTION_CSV_FIELDS,
    COLLECTIONS_CSV,
    COLLECTIONS_SUBDIR,
    REPO_URL,
)
from scripts.utils import write_output


def clone_repo(repo_url: str, branch: str, dest: Path):
    subprocess.run(
        ["git", "clone", "--depth", "1", "--branch", branch, repo_url, str(dest)],
        check=True,
    )


def extract_urls(metadata: dict, collection: str, slug: str) -> list[dict]:
    rows = []

    for site in metadata.get("websites") or []:
        if isinstance(site, dict):
            url = site.get("url", "")
            text = site.get("link-text", "")
        else:
            url = str(site)
            text = ""
        if url:
            rows.append(
                {
                    "collection": collection,
                    "slug": slug,
                    "link-url": url,
                    "link-text": text,
                    "type": "website",
                }
            )

    for field_type in ("api", "dataset"):
        field = metadata.get(field_type)
        if not field:
            continue
        if isinstance(field, dict):
            url = field.get("url", "")
            text = field.get("link-text", "")
            if url:
                rows.append(
                    {
                        "collection": collection,
                        "slug": slug,
                        "link-url": url,
                        "link-text": text,
                        "type": field_type,
                    }
                )
        elif isinstance(field, list):
            for item in field:
                if isinstance(item, dict):
                    url = item.get("url", "")
                    link_text = item.get("link-text", "")
                else:
                    url = str(item)
                    link_text = ""
                if url:
                    rows.append(
                        {
                            "collection": collection,
                            "slug": slug,
                            "link-url": url,
                            "link-text": link_text,
                            "type": field_type,
                        }
                    )

    return rows


def get_urls(collections_dir: Path) -> list[dict]:
    rows = []
    for topic_dir in sorted(collections_dir.iterdir()):
        if not topic_dir.is_dir():
            continue
        collection = topic_dir.name
        for md_file in sorted(topic_dir.glob("*.md")):
            try:
                f_matter = frontmatter.load(str(md_file))
            except Exception as exc:
                click.echo(f"Skipping {md_file}: {exc}", err=True)
            rows.extend(extract_urls(f_matter.metadata, collection, md_file.stem))
    return rows


@click.command()
@click.option("--branch", default="main", help="Git branch to clone.")
def get_collection_urls(branch):
    with tempfile.TemporaryDirectory() as tmp:
        dest = Path(tmp) / "datagovuk_find"
        click.echo(f"Cloning {REPO_URL} (branch: {branch})...")
        clone_repo(REPO_URL, branch, dest)

        collections_dir = dest / COLLECTIONS_SUBDIR
        click.echo(f"Reading collection files in {collections_dir}...")
        rows = get_urls(collections_dir)
        click.echo(f"Found {len(rows)} URLs across all collections.")

        output_path = Path(COLLECTIONS_CSV)
        write_output(output_path, rows, COLLECTION_CSV_FIELDS)
        click.echo(f"Wrote {len(rows)} rows to {output_path}")
