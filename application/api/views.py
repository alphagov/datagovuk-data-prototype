from flask import Blueprint, current_app, jsonify, request
from opensearchpy.exceptions import OpenSearchException, RequestError

from application.search.client import SearchNotConfigured, search
from application.search.query import (
    AVAILABLE_AS,
    COLLECTIONS,
    DATASETS,
    MAX_RESULT_WINDOW,
    MAX_SIZE,
    PAGE_SIZE,
    build_query,
    read_filters,
)

api_bp = Blueprint("api", __name__)


class InvalidParam(ValueError):
    """Raised for a query string param the caller got wrong - reported as a 400."""


def _positive_int(arg_name, default, maximum=None):
    val = request.args.get(arg_name)
    if val is None or val == "":
        return default
    try:
        value = int(val)
    except ValueError:
        raise InvalidParam(
            f"'{arg_name}' must be a whole number, got {val!r}"
        ) from None
    if value < 0:
        raise InvalidParam(f"'{arg_name}' must be 0 or greater, got {value}")
    return min(value, maximum) if maximum is not None else value


@api_bp.errorhandler(InvalidParam)
def handle_invalid_param(error):
    return jsonify(error=str(error)), 400


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


def _keyword(search_index):
    """Search single index and pass through response as is"""
    q = request.args.get("q", "").strip()
    filters = read_filters(search_index, request.args)

    available_as = []
    if search_index.available_as:
        available_as = [a for a in request.args.getlist("available_as") if a]
        unknown = sorted(set(available_as) - set(AVAILABLE_AS))
        if unknown:
            raise InvalidParam(
                f"'available_as' must be one of {', '.join(sorted(AVAILABLE_AS))}, "
                f"got {unknown}"
            )

    size = _positive_int("size", PAGE_SIZE, maximum=MAX_SIZE)
    from_ = _positive_int("from", 0)

    if from_ + size > MAX_RESULT_WINDOW:
        raise InvalidParam(
            f"'from' + 'size' must not exceed {MAX_RESULT_WINDOW}, got {from_ + size}"
        )

    body = build_query(
        search_index,
        q=q,
        available_as=available_as,
        filters=filters,
        size=size,
        _from=from_,
    )
    return jsonify(search(search_index, body))


@api_bp.route("/collections/keyword")
def collections_keyword():
    return _keyword(COLLECTIONS)


@api_bp.route("/directory/keyword")
def directory_keyword():
    return _keyword(DATASETS)
