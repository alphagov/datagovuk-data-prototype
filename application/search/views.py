from flask import (
    Blueprint,
    current_app,
    flash,
    render_template,
    request,
    url_for,
)

from application.search.client import SearchNotConfigured, get_client
from application.search.query import build_query, extract_facets, extract_results

search_bp = Blueprint("search", __name__)


@search_bp.app_template_global()
def _facet_url(name, value):
    args = request.args.to_dict(flat=False)
    current = args.get(name, [])
    (current.remove if value in current else current.append)(value)
    if current:
        args[name] = current
    else:
        args.pop(name, None)
    return url_for("search.keyword", **args)


@search_bp.route("/")
def index():
    breadcrumbs = [
        {"page": "Home", "href": url_for("frontend.index")},
        {"page": "Search"},
    ]
    return render_template("search/index.html", breadcrumbs=breadcrumbs)


@search_bp.route("/keyword")
def keyword():
    breadcrumbs = [
        {"page": "Home", "href": url_for("frontend.index")},
        {"page": "Search", "href": url_for("search.index")},
        {"page": "Keyword"},
    ]
    q = request.args.get("q", "").strip()
    collections = [c for c in request.args.getlist("collection") if c]
    available_as = [a for a in request.args.getlist("available_as") if a]

    # the search always runs — with no query and no filters it matches everything, so
    # landing on the page shows every topic and the full set of facet counts
    searched = True
    results = []
    facets = {}
    total = 0
    try:
        client = get_client()
        body = build_query(q, collections, available_as)
        resp = client.search(index=current_app.config["OPENSEARCH_INDEX"], body=body)
        total = resp["hits"]["total"]["value"]
        results = extract_results(resp["hits"]["hits"])
        facets = extract_facets(resp.get("aggregations", {}))
    except SearchNotConfigured:
        # if deployed without an OpenSearch domain configured flash no search yet
        flash("Search is not available yet — no OpenSearch domain is configured.")
        searched = False

    return render_template(
        "search/keyword.html",
        results=results,
        facets=facets,
        total=total,
        query=q,
        searched=searched,
        filtered_collections=collections,
        filtered_available_as=available_as,
        breadcrumbs=breadcrumbs,
    )
