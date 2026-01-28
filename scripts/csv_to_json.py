import click
import csv
import json


from pathlib import Path
from scripts.config import DATA_DIR


@click.command()
@click.argument("csv_file")
def to_json(csv_file):
    click.echo(f"Processing {csv_file}")
    file_path = Path(csv_file)
    title = file_path.stem.split("-")
    title = " ".join(title)

    data_dict = {"title": title, "data": []}
    with open(file_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            data_dict["data"].append(row)

    output = DATA_DIR / f"{file_path.stem}.json"
    with open(output, "w") as f:
        json.dump(data_dict, f, indent=2)
        print(f"Saved to {output}")
