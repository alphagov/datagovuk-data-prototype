import click
from scripts.company_formation import companies_formed_by_quarter


@click.group
def cli():
    pass


cli.add_command(companies_formed_by_quarter, name="companies")


if __name__ == "__main__":
    cli()
