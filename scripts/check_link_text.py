import csv
from pathlib import Path

import click

from scripts.config import COLLECTIONS_CSV


@click.command()
@click.option(
    "--input",
    "input_path",
    default=str(COLLECTIONS_CSV),
    help="Input CSV path.",
)
def check_link_text(input_path):
    """Report collection URLs that are missing link-text."""
    path = Path(input_path)
    if not path.exists():
        raise click.ClickException(f"CSV not found: {path}")

    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    missing = [r for r in rows if not r.get("link-text", "").strip()]

    if not missing:
        click.echo(f"All {len(rows)} URLs have link-text defined.")
        return

    click.echo(f"Found {len(missing)} URLs missing link-text:\n")
    for row in missing:
        click.echo(f"\t{row['collection']} / {row['slug']}")
        click.echo(f"\t{row['url']}")
        click.echo()
