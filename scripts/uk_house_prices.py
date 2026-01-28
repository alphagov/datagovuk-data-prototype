import pandas as pd
import httpx
import ssl
import truststore
import click

from io import StringIO
from scripts.config import DATA_DIR


URL = "https://publicdata.landregistry.gov.uk/market-trend-data/house-price-index-data/Average-prices-2025-11.csv"
OUTPUT_FILE = DATA_DIR / "summary-average-house-prices-2025-11.json"

REGIONS_OF_INTEREST = [
    "England",
    "Wales",
    "Scotland",
    "Northern Ireland",
    "North East",
    "North West",
    "Yorkshire and The Humber",
    "East Midlands",
    "West Midlands",
    "East of England",
    "London",
    "South East",
    "South West",
]

SORT_ORDER = [
    "England",
    "Northern Ireland",
    "Scotland",
    "Wales",
    "East Midlands",
    "East of England",
    "London",
    "North East",
    "North West",
    "South East",
    "South West",
    "West Midlands",
    "Yorkshire and The Humber",
]


def _download_csv(url):
    ctx = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    client = httpx.Client(verify=ctx)
    response = client.get(url)
    return pd.read_csv(StringIO(response.text))


def get_house_price_data(url: str) -> pd.DataFrame:
    df = _download_csv(url)

    df["Date"] = pd.to_datetime(df["Date"])
    latest_date = df["Date"].max()

    df_latest = df[df["Date"] == latest_date]
    df_regions = df_latest[df_latest["Region_Name"].isin(REGIONS_OF_INTEREST)]

    summary = df_regions[
        ["Region_Name", "Average_Price", "Monthly_Change", "Annual_Change"]
    ].rename(
        columns={
            "Region_Name": "region",
            "Average_Price": "average-price",
            "Monthly_Change": "percentage-monthly-change",
            "Annual_Change": "percentage-annual-change",
        }
    )

    summary["region"] = pd.Categorical(
        summary["region"],
        categories=SORT_ORDER,
        ordered=True,
    )

    summary = summary.sort_values("region").reset_index(drop=True)
    return summary


@click.command
def get_prices():
    table = get_house_price_data(URL)
    table.to_json(OUTPUT_FILE, orient="records")
    print(f"Wrote {OUTPUT_FILE}")
    print(table)
