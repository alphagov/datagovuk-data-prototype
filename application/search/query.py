"""Query building for the two opensearch indexes
The collections (markdown collection/topics) and the datasets (CKAN records)
live in separate indxes with facets but use a shared the query builder
just test code not to be copied for prod
"""

from dataclasses import dataclass, field

PAGE_SIZE = 20
MAX_SIZE = 200

# OpenSearch's index.max_result_window default - from + size - above this is rejected
# by the cluster so the API rejects it first
MAX_RESULT_WINDOW = 10000

FACET_SIZE = 25

# boost title matches to 3 x body matches
SEARCH_FIELDS = ["title^3", "body"]

AVAILABLE_AS = {
    "api": "has_api",
    "dataset": "has_dataset",
    "website": "has_website",
}

HIGHLIGHT = {
    "encoder": "html",
    "pre_tags": ["<mark>"],
    "post_tags": ["</mark>"],
    "fields": {
        "title": {"number_of_fragments": 0},
        "body": {"fragment_size": 160, "number_of_fragments": 1, "no_match_size": 160},
    },
}


@dataclass
class Facet:
    param: str
    field: str
    heading: str
    label_field: str = None


@dataclass
class SearchIndex:
    name: str
    index_key: str  # the app config key holding the index name
    facets: list
    # the has_* flags come from the markdown frontmatter - so collections only
    available_as: bool = False
    source_excludes: list = field(default_factory=lambda: ["body"])


COLLECTIONS = SearchIndex(
    name="collections",
    index_key="OPENSEARCH_COLLECTIONS_INDEX",
    facets=[Facet("collection", "collection", "Collection")],
    available_as=True,
)

DATASETS = SearchIndex(
    name="datasets",
    index_key="OPENSEARCH_DATASETS_INDEX",
    facets=[
        Facet("organisation", "organisation", "Organisation", "organisation_title"),
        Facet("format", "formats", "Format"),
        Facet("licence", "licence", "Licence", "licence_title"),
    ],
    source_excludes=["body", "resources", "metadata_rows"],
)


def _bucket(bucket):
    facet = {
        "key": bucket.get("key_as_string", bucket["key"]),
        "count": bucket["doc_count"],
    }
    label = bucket.get("label", {}).get("buckets")
    if label:
        facet["label"] = label[0]["key"]
    return facet


def extract_facets(aggregations):
    return {
        name: [_bucket(b) for b in aggregate.get("buckets", [])]
        for name, aggregate in aggregations.items()
    }


def extract_results(hits):
    return [{**hit["_source"], "highlight": hit.get("highlight", {})} for hit in hits]


def read_filters(search_index, args):
    """{param: [values]} off the query string, ignoring params this index doesn't have."""
    return {
        f.param: [v for v in args.getlist(f.param) if v] for f in search_index.facets
    }


def _agg(facet):
    body = {"terms": {"field": facet.field, "size": FACET_SIZE}}
    if facet.label_field:
        body["aggs"] = {"label": {"terms": {"field": facet.label_field, "size": 1}}}
    return body


def build_query(
    search_index, q="", available_as=(), filters=None, size=PAGE_SIZE, _from=0
):
    filters = filters or {}

    clauses = []
    for facet in search_index.facets:
        values = filters.get(facet.param)
        if values:
            clauses.append({"terms": {facet.field: values}})
    if search_index.available_as:
        for name, flag in AVAILABLE_AS.items():
            if name in available_as:
                clauses.append({"term": {flag: True}})

    if q:
        must = {
            "query_string": {
                "query": q,
                "fields": SEARCH_FIELDS,
                "default_operator": "AND",
            }
        }
    else:
        must = {"match_all": {}}

    aggs = {f.field: _agg(f) for f in search_index.facets}
    if search_index.available_as:
        aggs.update({f: {"terms": {"field": f}} for f in AVAILABLE_AS.values()})

    return {
        "size": size,
        "from": _from,
        "_source": {"excludes": search_index.source_excludes},
        "query": {"bool": {"must": [must], "filter": clauses}},
        "highlight": HIGHLIGHT,
        "aggs": aggs,
    }
