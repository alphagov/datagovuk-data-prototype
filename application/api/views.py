from flask import Blueprint, current_app, jsonify, request
from opensearchpy.exceptions import OpenSearchException, RequestError

from application.search.client import SearchNotConfigured, get_client
from application.search.query import build_query, extract_facets, extract_results

api_bp = Blueprint("api", __name__)


@api_bp.errorhandler(SearchNotConfigured)
def handle_search_not_configured(error):
    return jsonify(error=str(error), search_configured=False), 400


@api_bp.errorhandler(RequestError)
def handle_bad_query(error):
    return jsonify(error="Invalid search query"), 404


@api_bp.errorhandler(OpenSearchException)
def handle_search_unavailable(error):
    current_app.logger.exception("OpenSearch request failed")
    return jsonify(error="Search is unavailable"), 404


@api_bp.route("/keyword-search")
def keyword_search():
    # returns the same results and facets as used for HTML view
    # but if called with query string param 'raw' return opensearch result as is
    q = request.args.get("q", "").strip()
    collections = [c for c in request.args.getlist("collection") if c]
    available_as = [a for a in request.args.getlist("available_as") if a]

    # as with the HTML view, no query and no filters returns everything
    body = build_query(q, collections, available_as)
    resp = get_client().search(index=current_app.config["OPENSEARCH_INDEX"], body=body)

    if request.args.get("raw", None) is not None:
        # return the raw opensearch repsonse
        return jsonify(resp)

    return jsonify(
        query=q,
        total=resp["hits"]["total"]["value"],
        results=extract_results(resp["hits"]["hits"]),
        facets=extract_facets(resp.get("aggregations", {})),
    )
