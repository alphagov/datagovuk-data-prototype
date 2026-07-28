from flask import current_app
from opensearchpy import OpenSearch


class SearchNotConfigured(RuntimeError):
    """Raised when OPENSEARCH_URL is unset i.e. no OpenSearch domain is provisioned yet."""


def get_client():
    url = current_app.config.get("OPENSEARCH_URL", None)
    if url is None:
        raise SearchNotConfigured(
            "Search is not configured. Set OPENSEARCH_URL to enable it."
        )
    return OpenSearch(
        hosts=[url],
        use_ssl=False,
        verify_certs=False,
    )
