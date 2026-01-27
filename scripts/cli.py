import click
from scripts.company_formation import companies_formed_by_quarter
from scripts.csv_to_json import to_json
from scripts.food_standards import add_region_to_ratings


@click.group
def cli():
    pass


cli.add_command(companies_formed_by_quarter, name="companies")
cli.add_command(to_json, name="tojson")
cli.add_command(add_region_to_ratings, name="add-regions")


if __name__ == "__main__":
    cli()
