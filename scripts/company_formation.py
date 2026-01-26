import pandas as pd
import httpx
import truststore
import ssl
import json
import click
from io import StringIO
from scripts.config import DATA_DIR


def _download_csv(url):
    ctx = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    client = httpx.Client(verify=ctx)
    response = client.get(url)
    return pd.read_csv(StringIO(response.text))


def _get_quarter_label(date):
    quarter = (date.month - 1) // 3 + 1
    return f"Q{quarter} {date.year}"


def _extract_last_four_quarters(df, source):
    df_filtered = df[
        (df["Region"] == "UK")
        & (df["Corporate body type"] == "All companies")
        & (df["Attribute"] == "Incorporations")
    ].copy()

    if len(df_filtered) == 0:
        print("No incorporation data found.")
        return None

    df_filtered["Date"] = pd.to_datetime(df_filtered["Date"])
    df_filtered = df_filtered.sort_values("Date")

    last_four = df_filtered.tail(4)

    last_date = last_four["Date"].iloc[-1]
    last_quarter_label = _get_quarter_label(last_date)

    data = []
    for _, row in last_four.iterrows():
        quarter_label = _get_quarter_label(row["Date"])
        data.append({quarter_label: int(row["Value"])})

    return {
        "publisher": "Companies House",
        "title": f"Last four quarters to {last_quarter_label}",
        "data": data,
        "source": source,
    }


@click.command()
@click.argument("csv_url")
def companies_formed_by_quarter(csv_url):
    print(f"Downloading data from: {csv_url}")
    df = _download_csv(csv_url)
    print(f"Loaded {len(df)} rows")
    result = _extract_last_four_quarters(df, csv_url)
    if result is not None:
        output_file = DATA_DIR / "quaterly-company-formation.json"
        with open(output_file, "w") as f:
            json.dump(result, f, indent=2)
        print(f"Saved to {output_file}")
    else:
        print("No quarterly company formation data found")
