import csv

import click
from jinja2 import Template

from scripts.config import COLLECTION_URL, RESULTS_DIR, TESTING_DIR

template = Template("""
# data.gov.uk collection page checks
                    
This test uses Playwright to check the [collection content files](https://github.com/alphagov/datagovuk_find/tree/main/app/content/collections) from the datagovuk_find repository.

It fetches those files, extracts the list of urls (webistes, api, dataset) referred to the markdown frontmatter.

The tests visit the rendered html version of each collection page on data.gov.uk and ensures that:

- the links listed in the frontmatter are rendered on the page
- that those links are reachable
                    
                    
## Report

Using test results file: [results/{{source}}](results/{{source}})

{% if not report %}
No issues reported
{% else %}
{% for key, val in report.items() %}
## {{ key | replace("-", " ") | capitalize }}
Page: [{{base_url}}/{{val['collection']}}/{{key}}]({{base_url}}/{{val['collection']}}/{{key}})

{% if val['not-on-page'] %}
Check the following links are on the page above - the test does report false positives:
{% for link in  val['not-on-page'] %}
- {{link}}
{% endfor %}
{% endif %}
            
{% if val['not-reachable'] %}
The following links were not reachable during test
{% for link in  val['not-reachable'] %}
- [{{link}}]({{link}})
{% endfor %}
{% endif %}
{% endfor %}
{% endif %}
""")


def _get_most_recent_result(directory):
    latest = max(directory.glob("*.csv"), key=lambda f: f.stat().st_mtime)
    return latest


def _write_markdown(source, report, template, base_url, output_dir):
    md_file_path = output_dir / "README.md"
    with open(md_file_path, "w") as f:
        context = {"source": source, "report": report, "base_url": base_url}
        content = template.render(context)
        f.write(content)


@click.command()
def create_report():
    latest = _get_most_recent_result(RESULTS_DIR)
    click.echo(f"Reporting from {latest}")
    report = {}
    with open(latest) as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["on-page"] == "False" or row["reachable"] == "False":
                slug = row["slug"]
                if slug not in report:
                    report[slug] = {
                        "collection": row["collection"],
                        "not-on-page": [],
                        "not-reachable": [],
                    }
                if row["on-page"] == "False":
                    report[slug]["not-on-page"].append(row["link-url"])
                if row["reachable"] == "False":
                    report[slug]["not-reachable"].append(row["link-url"])

    _write_markdown(latest.name, report, template, COLLECTION_URL, TESTING_DIR)
