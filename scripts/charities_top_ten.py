import csv
import json
from collections import defaultdict

import click

from scripts.config import DATA_DIR, REFERENCE_DATA_DIR


@click.command
def top_ten():
    csv_file = REFERENCE_DATA_DIR / "charity-commission-top-10-charites-by-category.csv"
    with open(csv_file) as f:
        reader = csv.DictReader(f)
        categories = defaultdict(list)
        for row in reader:
            type = row["type"]
            categories[type].append(row)

    out_file = DATA_DIR / "charity-commission-top-10-charites-by-category.json"
    data = {
        "title": "Charity commission top-10-charites bycategory",
        "publisher": "Charities commission",
        "source": "https://register-of-charities.charitycommission.gov.uk/en/sector-data/top-10-charities",
        "data": categories,
    }

    with open(out_file, "w") as f:
        json.dump(data, f, indent=2)
        print(f"Saved to {out_file}")


if __name__ == "__main__":
    top_ten()
