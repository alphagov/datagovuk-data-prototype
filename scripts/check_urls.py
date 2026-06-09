import csv
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote, urlparse, urlunparse

import click
from playwright.sync_api import sync_playwright

from scripts.config import COLLECTION_URL, COLLECTIONS_CSV, RESULTS_CSV, RESULTS_DIR
from scripts.utils import write_output


def normalize_url(url: str) -> str:
    """Normalize a URL for comparison: lowercase scheme/host, strip trailing slash, decode percent-encoding."""
    url = unquote(url).strip()
    parsed = urlparse(url)
    host = parsed.hostname or ""
    host = host.removeprefix("www.")
    path = parsed.path.rstrip("/")
    return urlunparse(
        (parsed.scheme.lower(), host, path, parsed.params, parsed.query, "")
    )


def get_page_hrefs(page) -> set[str]:
    """Extract all href attributes from <a> tags on the current page."""
    return set(
        normalize_url(href)
        for href in page.eval_on_selector_all("a[href]", "els => els.map(e => e.href)")
        if href
    )


def check_reachable(page, url: str) -> bool:
    """Navigate to a URL and return True if the page loaded"""
    try:
        resp = page.goto(url, wait_until="domcontentloaded", timeout=15000)
        return resp is not None
    except Exception:
        return False


def check_collection_pages(rows: list[dict], headed: bool = False, slow_mo: int = 0):
    rows_by_page = defaultdict(list)
    for row in rows:
        rows_by_page[(row["collection"], row["slug"])].append(row)

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=not headed, slow_mo=slow_mo)
        context = browser.new_context()
        page = context.new_page()

        for (collection, slug), slug_rows in rows_by_page.items():
            collection_page_url = f"{COLLECTION_URL}/{collection}/{slug}"
            click.echo(f"  Checking {collection_page_url}")
            try:
                page.goto(
                    collection_page_url, wait_until="domcontentloaded", timeout=15000
                )
                hrefs = get_page_hrefs(page)
            except Exception as exc:
                click.echo(f"Could not load page: {exc}", err=True)
                for row in slug_rows:
                    row["on-page"] = None
                    row["reachable"] = None
                continue

            for row in slug_rows:
                url = normalize_url(row["link-url"])
                row["on-page"] = url in hrefs

            # Check reachability in a separate browser tab
            check_page = context.new_page()
            for row in slug_rows:
                row["reachable"] = check_reachable(check_page, row["link-url"])
            check_page.close()

        browser.close()


@click.command()
@click.option(
    "--input",
    "input_path",
    default=str(COLLECTIONS_CSV),
    help="Input CSV path.",
)
@click.option(
    "--headed", is_flag=True, default=False, help="Run browser in headed mode."
)
@click.option(
    "--slow-mo", default=500, help="Delay between actions in ms (headed mode)."
)
def check_urls(input_path, headed, slow_mo):
    path = Path(input_path)
    if not path.exists():
        raise click.ClickException(f"CSV not found: {path}")

    with open(path, newline="") as f:
        rows = list(csv.DictReader(f))

    click.echo(f"Checking {len(rows)} URLs across collection pages...")
    check_collection_pages(rows, headed=headed, slow_mo=slow_mo if headed else 0)

    reachable = sum(1 for r in rows if r.get("reachable") is True)
    click.echo(f"Results: {reachable}/{len(rows)} reachable")

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M")
    output_path = RESULTS_DIR / f"collection-check-{timestamp}.csv"
    write_output(output_path, rows, RESULTS_CSV)
    click.echo(f"Wrote {len(rows)} rows to {output_path}")
