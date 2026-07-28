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
    # all that is needed to turn search on — there is no second switch.
    OPENSEARCH_URL = os.getenv("OPENSEARCH_URL")
    OPENSEARCH_INDEX = os.getenv("OPENSEARCH_INDEX", "topics")


class DevelopmentConfig(Config):
    DEBUG = True
    WTF_CSRF_ENABLED = False
    # compose sets this; the fallback keeps `flask run` outside docker working.
    OPENSEARCH_URL = os.getenv("OPENSEARCH_URL", "http://opensearch:9200")


class TestConfig(Config):
    TESTING = True
