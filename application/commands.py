from flask import current_app
from flask.cli import AppGroup

from application.search.client import get_client
from application.search.query import COLLECTIONS, DATASETS
from application.utils import (
    COLLECTIONS_MAPPING,
    DATASETS_MAPPING,
    SOLR_FILE,
    bulk_index,
    create_index,
    iter_documents,
    iter_solr_documents,
)

sandbox_cli = AppGroup("sbox")


def _rebuild(client, search_index, mapping, documents, source):
    index_name = current_app.config[search_index.index_key]
    create_index(client, index_name, mapping)
    count, errors = bulk_index(client, index_name, documents)
    print(f"Indexed {count} {search_index.name} from {source} into '{index_name}'")
    if errors:
        print(f"Errors: {errors}")
    client.indices.refresh(index=index_name)


@sandbox_cli.command(name="index")
def index():
    client = get_client()
    collections_dir = current_app.config["COLLECTIONS_DIR"]

    _rebuild(
        client,
        COLLECTIONS,
        COLLECTIONS_MAPPING,
        iter_documents(collections_dir),
        collections_dir,
    )
    _rebuild(
        client,
        DATASETS,
        DATASETS_MAPPING,
        iter_solr_documents(),
        f"data/{SOLR_FILE}",
    )
