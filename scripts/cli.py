import click
from scripts.company_formation import companies_formed_by_quarter
from scripts.csv_to_json import to_json
from scripts.aggregate_fhrs_ratings_by_region import aggregate


@click.group
def cli():
    pass


cli.add_command(companies_formed_by_quarter, name="companies")
cli.add_command(to_json, name="tojson")
cli.add_command(aggregate, name="ratings")


if __name__ == "__main__":
    cli()
