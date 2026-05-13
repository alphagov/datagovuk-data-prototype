import os


class Config:
    APP_ROOT = os.path.abspath(os.path.dirname(__file__))
    PROJECT_ROOT = os.path.abspath(os.path.join(APP_ROOT, os.pardir))
    SECRET_KEY = os.environ["SECRET_KEY"]
    CONTENT_DIR = os.path.join(APP_ROOT, "content")
    COLLECTIONS_DIR = os.path.join(CONTENT_DIR, "collections")
    DATABASE_URL = os.getenv("DATABASE_URL")
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = False
    EMBEDDING_MODEL = "Snowflake/snowflake-arctic-embed-s"
    EMBEDDING_DIM = (
        384  # snowflake-arctic-embed-s: small dim for local CPU inference without GPU
    )
    CKAN_PACKAGE_SEARCH_URL = os.getenv(
        "CKAN_PACKAGE_SEARCH_URL",
        "https://ckan.publishing.service.gov.uk/api/action/package_search",
    )

    DEBUG = False
    SEARCH_ENABLED = True


class DevelopmentConfig(Config):
    DEBUG = True
    WTF_CSRF_ENABLED = False


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = (
        "postgresql://postgres:password@test_db:5432/discover_test"
    )


class ProductionConfig(Config):
    SEARCH_ENABLED = False
