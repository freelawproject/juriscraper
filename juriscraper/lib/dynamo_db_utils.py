import datetime
import hashlib
import hmac
import json

import requests


def get_temp_credentials(identity_id: str, region: str) -> dict:
    """Retrieve temporary AWS credentials for a given Cognito identity.

    :param identity_id (str): The Cognito identity ID.
    :param region (str): The AWS region.
    :return dict: Dictionary containing temporary AWS credentials.
    """

    response = requests.post(
        f"https://cognito-identity.{region}.amazonaws.com/",
        headers={
            "Content-Type": "application/x-amz-json-1.1",
            "X-Amz-Target": "AWSCognitoIdentityService.GetCredentialsForIdentity",
        },
        data=json.dumps({"IdentityId": f"{region}:{identity_id}"}),
    )
    response.raise_for_status()
    return response.json()["Credentials"]


def generate_signature_headers(
    payload: str,
    creds: dict,
    region: str,
    signed_headers: str,
    target: str,
    service: str = "dynamodb",
) -> dict:
    """Generate AWS Signature v4 headers for DynamoDB requests.

    :param payload (str): The request payload as a JSON string.
    :param creds (dict): Temporary AWS credentials.
    :param region (str): AWS region.
    :param signed_headers (str): Semicolon-separated list of headers to sign.
    :param target (str): The X-Amz-Target value for the DynamoDB API.
    :param service (str, optional): AWS service name. Defaults to 'dynamodb'.
    :return dict: Dictionary of headers for the signed DynamoDB request.
    """

    access_key = creds["AccessKeyId"]
    secret_key = creds["SecretKey"]
    session_token = creds["SessionToken"]
    host = f"{service}.{region}.amazonaws.com"

    t = datetime.datetime.utcnow()
    amz_date = t.strftime("%Y%m%dT%H%M%SZ")
    date_stamp = t.strftime("%Y%m%d")

    payload_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    content_type = "application/x-amz-json-1.0"

    # Canonical headers must be in alphabetical order and include all signed headers
    canonical_headers_dict = {
        "content-type": content_type,
        "host": host,
        "x-amz-content-sha256": payload_hash,
        "x-amz-date": amz_date,
        "x-amz-security-token": session_token,
        "x-amz-target": target,
    }
    # Only include headers present in signed_headers
    canonical_headers = ""
    for header in sorted(signed_headers.split(";")):
        if header in canonical_headers_dict:
            canonical_headers += f"{header}:{canonical_headers_dict[header]}\n"

    canonical_request = "\n".join(
        [
            "POST",
            "/",
            "",  # query string
            canonical_headers,
            signed_headers,
            payload_hash,
        ]
    )

    algorithm = "AWS4-HMAC-SHA256"
    credential_scope = f"{date_stamp}/{region}/{service}/aws4_request"
    string_to_sign = "\n".join(
        [
            algorithm,
            amz_date,
            credential_scope,
            hashlib.sha256(canonical_request.encode("utf-8")).hexdigest(),
        ]
    )

    def sign(key: bytes, msg: str | bytes) -> bytes:
        """Create an HMAC-SHA256 signature.

        :param key: The key to use for signing (bytes).
        :param msg: The message to sign (str or bytes).
        :return: The HMAC-SHA256 signature as bytes.
        """

        if isinstance(msg, str):
            msg = msg.encode("utf-8")
        return hmac.new(key, msg, hashlib.sha256).digest()

    def get_signature_key(
        key: str, date_stamp: str, region_name: str, service_name: str
    ) -> bytes:
        """Generate the AWS Signature v4 signing key.

        :param key: AWS secret access key.
        :param date_stamp: Date in YYYYMMDD format.
        :param region_name: AWS region name.
        :param service_name: AWS service name.
        :return: The derived signing key as bytes.
        """

        kDate = sign(("AWS4" + key).encode("utf-8"), date_stamp)
        kRegion = sign(kDate, region_name)
        kService = sign(kRegion, service_name)
        return sign(kService, "aws4_request")

    signing_key = get_signature_key(secret_key, date_stamp, region, service)
    signature = hmac.new(
        signing_key, string_to_sign.encode("utf-8"), hashlib.sha256
    ).hexdigest()

    authorization = (
        f"{algorithm} "
        f"Credential={access_key}/{credential_scope}, "
        f"SignedHeaders={signed_headers}, "
        f"Signature={signature}"
    )

    return {
        "Content-Type": content_type,
        "X-Amz-Date": amz_date,
        "X-Amz-Target": target,
        "X-Amz-Security-Token": session_token,
        "X-Amz-Content-Sha256": payload_hash,
        "Authorization": authorization,
    }


def query_dynamodb(
    identity_id: str,
    region: str,
    payload_dict: dict,
    signed_headers: str,
    target: str,
) -> dict:
    """Query DynamoDB using temporary credentials and signed headers.

    :param identity_id (str): The Cognito identity ID.
    :param region (str): The AWS region.
    :param payload_dict (dict): The request payload as a dictionary.
    :param signed_headers (str): Semicolon-separated list of headers to sign.
    :param target (str): The X-Amz-Target value for the DynamoDB API.
    :return dict: JSON response from DynamoDB.
    """

    creds = get_temp_credentials(identity_id, region)

    target = f"DynamoDB_20120810.{target}"
    payload = json.dumps(payload_dict)
    headers = generate_signature_headers(
        payload, creds, region, signed_headers, target
    )

    endpoint = f"https://dynamodb.{region}.amazonaws.com/"
    response = requests.post(endpoint, headers=headers, data=payload)

    response.raise_for_status()
    return response.json()
