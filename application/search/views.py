import requests
import sqlalchemy as sa
from flask import Blueprint, current_app, render_template, request, url_for
from sqlalchemy.orm import joinedload

from application.embeddings import embed
from application.models import Topic

RRF_K = 60  # standard reciprocal-rank-fusion constant
CANDIDATE_POOL = 30
RESULT_LIMIT = 20

search_bp = Blueprint(
    "search",
    __name__,
    url_prefix="/search",
    template_folder="templates",
)


@search_bp.route("/")
def index():
    breadcrumbs = [
        {"page": "Home", "href": url_for("frontend.index")},
        {"page": "Search"},
    ]
    return render_template("search.html", breadcrumbs=breadcrumbs)


@search_bp.route("/postgres")
def postgres():
    q = request.args.get("q", "").strip()
    include_ckan = request.args.get("include_ckan") == "1"
    results = []
    ckan_results = []

    if q:
        ts_query = sa.func.websearch_to_tsquery("english", q)
        rank_expr = sa.func.ts_rank(Topic.search_vector, ts_query)

        results = (
            Topic.query.filter(Topic.search_vector.op("@@")(ts_query))
            .order_by(rank_expr.desc())
            .options(joinedload(Topic.collection))
            .all()
        )

        if include_ckan:
            ckan_url = current_app.config["CKAN_PACKAGE_SEARCH_URL"]
            ckan_results = ckan_package_search(ckan_url, q)

    breadcrumbs = [
        {"page": "Home", "href": url_for("frontend.index")},
        {"page": "Search", "href": url_for("search.index")},
        {"page": "Postgres keyword search"},
    ]
    return render_template(
        "pgsearch.html",
        results=results,
        include_ckan=include_ckan,
        ckan_results=ckan_results,
        query=q,
        breadcrumbs=breadcrumbs,
    )


@search_bp.route("/postgres-hybrid")
def postgres_hybrid():
    q = request.args.get("q", "").strip()
    results = []
    fts_only_ids = set()
    vector_only_ids = set()

    if q:
        ts_query = sa.func.websearch_to_tsquery("english", q)

        fts_topics = (
            Topic.query.filter(Topic.search_vector.op("@@")(ts_query))
            .order_by(sa.func.ts_rank(Topic.search_vector, ts_query).desc())
            .options(joinedload(Topic.collection))
            .limit(CANDIDATE_POOL)
            .all()
        )
        fts_ranking = {t.id: rank for rank, t in enumerate(fts_topics)}

        query_embedding = embed(q)
        vector_topics = (
            Topic.query.filter(Topic.embedding.is_not(None))
            .order_by(Topic.embedding.cosine_distance(query_embedding))
            .options(joinedload(Topic.collection))
            .limit(CANDIDATE_POOL)
            .all()
        )
        vector_ranking = {t.id: rank for rank, t in enumerate(vector_topics)}

        topics_by_id = {t.id: t for t in fts_topics + vector_topics}

        fused = _reciprocal_rank_fusion(fts_ranking, vector_ranking)
        results = [topics_by_id[doc_id] for doc_id, _ in fused[:RESULT_LIMIT]]

        fts_only_ids = fts_ranking.keys() - vector_ranking.keys()
        vector_only_ids = vector_ranking.keys() - fts_ranking.keys()

    breadcrumbs = [
        {"page": "Home", "href": url_for("frontend.index")},
        {"page": "Search", "href": url_for("search.index")},
        {"page": "Postgres keyword + semantic"},
    ]
    return render_template(
        "pgsearch_hybrid.html",
        results=results,
        query=q,
        fts_only_ids=fts_only_ids,
        vector_only_ids=vector_only_ids,
        breadcrumbs=breadcrumbs,
    )


def _reciprocal_rank_fusion(fts_ranking, vector_ranking):
    """Merge two ranked id lists by summing 1 / (K + rank) for each id."""
    scores: dict = {}
    for ranking in (fts_ranking, vector_ranking):
        for doc_id, rank in ranking.items():
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (RRF_K + rank)
    return sorted(scores.items(), key=lambda item: item[1], reverse=True)


def ckan_package_search(url, query):
    try:
        resp = requests.get(url, params={"q": query}, timeout=25)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException:
        return []
    except ValueError:
        return []

    packages = data.get("result", {}).get("results", [])
    return [
        {
            "title": pkg.get("title", pkg.get("name", "Untitled")),
            "url": f"https://www.data.gov.uk/dataset/{pkg['name']}",
        }
        for pkg in packages
        if pkg.get("name")
    ]
