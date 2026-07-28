from flask import current_app
from flask.cli import AppGroup

from application.search.client import get_client
from application.utils import bulk_index, create_index

sandbox_cli = AppGroup("sbox")


@sandbox_cli.command(name="index")
def index():
    """Rebuild the search index from the markdown in content/collections/.

    Run with `flask sbox index` (or `just index` against the running stack).
    The index is dropped and recreated, so it is safe to re-run any time the
    markdown changes.
    """
    client = get_client()
    index_name = current_app.config["OPENSEARCH_INDEX"]
    collections_dir = current_app.config["COLLECTIONS_DIR"]

    create_index(client, index_name)
    print(f"Created index '{index_name}'")

    success, errors = bulk_index(client, index_name, collections_dir)
    print(f"Indexed {success} documents from {collections_dir}")
    if errors:
        print(f"Errors: {errors}")
