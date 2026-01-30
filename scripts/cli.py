import click

from scripts.aggregate_fhrs_ratings_by_region import aggregate
from scripts.charities_top_ten import top_ten
from scripts.company_formation import companies_formed_by_quarter
from scripts.csv_to_json import to_json
from scripts.uk_house_prices import get_prices


@click.group
def cli():
    pass


cli.add_command(companies_formed_by_quarter, name="companies")
cli.add_command(to_json, name="tojson")
cli.add_command(aggregate, name="food-ratings")
cli.add_command(get_prices, name="house-prices")
cli.add_command(top_ten, name="topten")

if __name__ == "__main__":
    cli()
