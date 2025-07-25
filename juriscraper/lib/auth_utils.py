import datetime
import hashlib
import hmac
import os

from juriscraper.AbstractSite import logger
from juriscraper.OpinionSite import OpinionSite


def set_api_token_header(site: OpinionSite) -> None:
    """
    Puts the NY_API_TOKEN in the X-Api-Token header
    Creates the Site.headers attribute, copying the
    scraper_site.request[headers]

    :param scraper_site: a Site Object
    :returns: None
    """
    if site.test_mode_enabled():
        return
    api_token = os.environ.get("NY_API_TOKEN", None)
    if not api_token:
        logger.warning(
            "NY_API_TOKEN environment variable is not set. "
            f"It is required for scraping New York Court: {site.court_id}"
        )
        return
    site.request["headers"]["X-APIKEY"] = api_token
    site.needs_special_headers = True


def generate_aws_sigv4_headers(
    payload: str,
    table_name: str = None,
    creds: dict = None,
    signed_headers: str = "host;x-amz-date;x-amz-security-token;x-amz-target",
    target: str = "DynamoDB_20120810.Scan",
    service: str = "dynamodb",
    region: str = "us-west-2",
):
    """Generate AWS Signature Version 4 headers for a DynamoDB Scan request.

    This function builds the necessary SigV4 signing information and returns
    a complete set of HTTP headers you can pass to `requests` (or any HTTP
    client) to perform an authenticated DynamoDB Scan.
    :param payload: The JSON payload to send in the request body
    :param table_name: Table to scan or query
    :param creds: temp dictionary of credentials
    :param signed_headers: headers to include
    :param target: The request
    :param service: type of query
    :param region: the aws region
    :return: signed headers to use to query db
    """
    # 1. Prepare SigV4 signing
    now = datetime.datetime.utcnow()
    amz_date = now.strftime("%Y%m%dT%H%M%SZ")
    date_stamp = now.strftime("%Y%m%d")
    payload_hash = hashlib.sha256(payload.encode()).hexdigest()
    host = f"{service}.{region}.amazonaws.com"

    # Canonical headers
    canonical_headers = []
    headers_dict = {
        "content-type": "application/x-amz-json-1.0",
        "host": host,
        "x-amz-content-sha256": payload_hash,
        "x-amz-date": amz_date,
        "x-amz-security-token": creds["SessionToken"],
        "x-amz-target": target,
    }
    for h in sorted(signed_headers.split(";")):
        canonical_headers.append(f"{h}:{headers_dict[h]}\n")
    canonical_headers_str = "".join(canonical_headers)

    # Create canonical request
    canonical_request = "\n".join(
        ["POST", "/", "", canonical_headers_str, signed_headers, payload_hash]
    )

    algorithm = "AWS4-HMAC-SHA256"
    credential_scope = f"{date_stamp}/{region}/{service}/aws4_request"

    string_to_sign = "\n".join(
        [
            algorithm,
            amz_date,
            credential_scope,
            hashlib.sha256(canonical_request.encode()).hexdigest(),
        ]
    )

    # Signing key derivation
    def sign(key, msg):
        return hmac.new(key, msg.encode(), hashlib.sha256).digest()

    k_date = sign(("AWS4" + creds["SecretKey"]).encode(), date_stamp)
    k_region = sign(k_date, region)
    k_service = sign(k_region, service)
    k_signing = sign(k_service, "aws4_request")

    signature = hmac.new(
        k_signing, string_to_sign.encode(), hashlib.sha256
    ).hexdigest()

    return {
        "Content-Type": "application/x-amz-json-1.0",
        "X-Amz-Date": amz_date,
        "X-Amz-Security-Token": creds["SessionToken"],
        "X-Amz-Target": target,
        "Authorization": (
            f"{algorithm} Credential={creds['AccessKeyId']}/{credential_scope}, "
            f"SignedHeaders={signed_headers}, Signature={signature}"
        ),
        "X-Amz-Content-Sha256": payload_hash,
    }
