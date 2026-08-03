from flask import (
    Blueprint,
    flash,
    render_template,
    request,
    url_for,
)

from application.search.client import SearchNotConfigured, search
from application.search.query import (
    COLLECTIONS,
    DATASETS,
    MAX_RESULT_WINDOW,
    PAGE_SIZE,
    build_query,
    extract_facets,
    extract_results,
    read_filters,
)

search_bp = Blueprint("search", __name__)

# each results page has a JSON twin taking the same query string
API_ENDPOINTS = {
    "search.collections": "api.collections_keyword",
    "search.directory": "api.directory_keyword",
}


def _offset():
    try:
        value = int(request.args.get("from", 0))
    except ValueError:
        return 0
    return max(0, min(value, MAX_RESULT_WINDOW - PAGE_SIZE))


def _self_url(args):
    return url_for(request.endpoint or "search.index", **args)


@search_bp.app_template_global()
def _facet_url(name, value):
    args = request.args.to_dict(flat=False)
    current = args.get(name, [])
    (current.remove if value in current else current.append)(value)
    if current:
        args[name] = current
    else:
        args.pop(name, None)
    args.pop("from", None)
    return _self_url(args)


@search_bp.app_template_global()
def _page_url(from_):
    args = request.args.to_dict(flat=False)
    if from_:
        args["from"] = [str(from_)]
    else:
        args.pop("from", None)
    return _self_url(args)


@search_bp.app_template_global()
def _clear_url():
    q = request.args.get("q", "").strip()
    return _self_url({"q": [q]} if q else {})


@search_bp.app_template_global()
def _api_url():
    """The search you're looking at, as JSON."""
    return url_for(API_ENDPOINTS[request.endpoint], **request.args.to_dict(flat=False))


def _context(search_index):
    q = request.args.get("q", "").strip()
    available_as = [a for a in request.args.getlist("available_as") if a]
    filters = read_filters(search_index, request.args)
    from_ = _offset()

    context = {
        "search_index": search_index,
        "query": q,
        "filters": filters,
        "filtered_available_as": available_as,
        "from_": from_,
        "page_size": PAGE_SIZE,
        "searched": True,
        "results": [],
        "facets": {},
        "total": 0,
    }

    try:
        body = build_query(
            search_index,
            q=q,
            available_as=available_as,
            filters=filters,
            _from=from_,
        )
        resp = search(search_index, body)
    except SearchNotConfigured:
        # if deployed without an Opensearch domain configured flash message
        flash("Search is not available yet: no OpenSearch domain is configured.")
        context["searched"] = False
        return context

    context["total"] = resp["hits"]["total"]["value"]
    context["results"] = extract_results(resp["hits"]["hits"])
    context["facets"] = extract_facets(resp.get("aggregations", {}))
    return context


@search_bp.route("/")
def index():
    breadcrumbs = [
        {"page": "Home", "href": url_for("frontend.index")},
        {"page": "Search"},
    ]
    return render_template("search/index.html", breadcrumbs=breadcrumbs)


@search_bp.route("/collections/keyword")
def collections():
    breadcrumbs = [
        {"page": "Home", "href": url_for("frontend.index")},
        {"page": "Search", "href": url_for("search.index")},
        {"page": "Collections"},
    ]
    return render_template(
        "search/collections.html",
        breadcrumbs=breadcrumbs,
        **_context(COLLECTIONS),
    )


@search_bp.route("/directory/keyword")
def directory():
    breadcrumbs = [
        {"page": "Home", "href": url_for("frontend.index")},
        {"page": "Search", "href": url_for("search.index")},
        {"page": "Data directory"},
    ]
    return render_template(
        "search/directory.html",
        breadcrumbs=breadcrumbs,
        **_context(DATASETS),
    )
