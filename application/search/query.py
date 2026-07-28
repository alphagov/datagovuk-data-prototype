RESULT_SIZE = 100
# only approx 80 topics at the moment

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


def extract_facets(aggregations):
    return {
        name: [
            {"key": b["key"], "count": b["doc_count"]}
            for b in aggregate.get("buckets", [])
        ]
        for name, aggregate in aggregations.items()
    }


def extract_results(hits):
    return [{**hit["_source"], "highlight": hit.get("highlight", {})} for hit in hits]


def build_query(q, collections, available_as, size=RESULT_SIZE):
    filters = []
    if collections:
        filters.append({"terms": {"collection": collections}})
    for name, field in AVAILABLE_AS.items():
        if name in available_as:
            filters.append({"term": {field: True}})

    if not q:
        must = {"match_all": {}}
    else:
        must = {
            "query_string": {
                "query": q,
                "fields": SEARCH_FIELDS,
                "default_operator": "AND",
            }
        }

    return {
        "size": size,
        "_source": {"excludes": ["body"]},
        "query": {"bool": {"must": [must], "filter": filters}},
        "highlight": HIGHLIGHT,
        "aggs": {
            "collections": {"terms": {"field": "collection"}},
            **{field: {"terms": {"field": field}} for field in AVAILABLE_AS.values()},
        },
    }
