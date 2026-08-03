import boto3
from flask import current_app
from opensearchpy import OpenSearch, Urllib3AWSV4SignerAuth


class SearchNotConfigured(RuntimeError):
    """AWS Opensearch domain is provisioned yet"""


def get_client():
    url = current_app.config.get("OPENSEARCH_URL", None)
    if url is None:
        raise SearchNotConfigured(
            "Search is not configured. Set OPENSEARCH_URL to enable it."
        )
    if url.startswith("https://"):
        # then use AWS Opensearch with requests signed as the ECS task role.
        auth = Urllib3AWSV4SignerAuth(
            boto3.Session().get_credentials(),
            current_app.config["AWS_REGION"],
            "es",  # managed Opensearch
        )
        return OpenSearch(
            hosts=[url],
            http_auth=auth,
            use_ssl=True,
            verify_certs=True,
        )

    else:
        # use local dev container in compose
        return OpenSearch(
            hosts=[url],
            use_ssl=False,
            verify_certs=False,
        )


def search(search_index, body):
    return get_client().search(
        index=current_app.config[search_index.index_key], body=body
    )
