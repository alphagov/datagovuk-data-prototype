from flask import (
    Blueprint,
    abort,
    current_app,
    redirect,
    render_template,
    url_for,
)
from opensearchpy.exceptions import NotFoundError

from application.search.client import SearchNotConfigured, get_client
from application.search.query import DATASETS

datasets_bp = Blueprint("datasets", __name__, template_folder="../templates")


 # Note we maintain the url with id and slug as in current directory
@datasets_bp.route("/dataset/<dataset_id>/<slug>")
def dataset(dataset_id, slug):
    """Render a single CKAN dataset from the search index which is the
    display store for datasets so this is a direct get by id not a search.
    """
    try:
        client = get_client()
    except SearchNotConfigured:
        abort(503)

    try:
        doc = client.get(index=current_app.config[DATASETS.index_key], id=dataset_id)[
            "_source"
        ]
    except NotFoundError:
        abort(404)

    breadcrumbs = [
        {"page": "Home", "href": url_for("frontend.index")},
        {"page": "Search", "href": url_for("search.index")},
        {"page": doc.get("title", slug)},
    ]
    return render_template("dataset.html", doc=doc, breadcrumbs=breadcrumbs)
