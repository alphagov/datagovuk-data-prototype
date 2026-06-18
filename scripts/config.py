from pathlib import Path

COLLECTION_CSV_FIELDS = ["collection", "slug", "link-url", "link-text", "type"]
RESULTS_CSV = COLLECTION_CSV_FIELDS + ["on-page", "reachable"]

DATA_GOV_URL = "https://data.gov.uk"
COLLECTION_URL = DATA_GOV_URL + "/collections"

BASE_DIR = Path(__file__).resolve().parent.parent
COLLECTIONS_CSV = BASE_DIR / "testing" / "collections" / "collection-urls.csv"
TESTING_DIR = BASE_DIR / "testing"
RESULTS_DIR = TESTING_DIR / "results"
REPO_URL = "https://github.com/alphagov/datagovuk.git"
COLLECTIONS_SUBDIR = "content/collections"
