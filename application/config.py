import os


class Config:
    APP_ROOT = os.path.abspath(os.path.dirname(__file__))
    PROJECT_ROOT = os.path.abspath(os.path.join(APP_ROOT, os.pardir))
    SECRET_KEY = os.environ["SECRET_KEY"]

    CONTENT_DIR = os.path.join(APP_ROOT, "content")
    COLLECTIONS_DIR = os.path.join(CONTENT_DIR, "collections")

    # No default: until the OpenSearch domain is provisioned and OPENSEARCH_URL is set on
    # the task definition, this stays None and the search endpoints report themselves as
    # unconfigured rather than failing against an unreachable host. Setting the env var is
    # all that is needed to turn search on - there is no second switch.
    OPENSEARCH_URL = os.getenv("OPENSEARCH_URL")

    # Two separate indices, deliberately not merged: the collections are curated
    # markdown topics, the datasets are CKAN records, and their fields and facets
    # don't line up. Each has its own mapping, routes and API endpoint.
    OPENSEARCH_COLLECTIONS_INDEX = os.getenv(
        "OPENSEARCH_COLLECTIONS_INDEX", "collections"
    )
    OPENSEARCH_DATASETS_INDEX = os.getenv("OPENSEARCH_DATASETS_INDEX", "datasets")

    # Only used when OPENSEARCH_URL is https, to sign requests to AWS OpenSearch
    # Service. ECS does not inject this the way Lambda does, so the task
    # definition has to set it explicitly.
    AWS_REGION = os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION")


class DevelopmentConfig(Config):
    DEBUG = True
    WTF_CSRF_ENABLED = False
    # compose sets this; the fallback keeps `flask run` outside docker working.
    OPENSEARCH_URL = os.getenv("OPENSEARCH_URL", "http://opensearch:9200")


class TestConfig(Config):
    TESTING = True
