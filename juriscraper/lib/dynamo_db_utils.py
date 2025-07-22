import datetime
import hashlib
import hmac
import json

import requests


def get_temp_credentials(identity_id: str, region: str) -> dict:
    response = requests.post(
        f"https://cognito-identity.{region}.amazonaws.com/",
        headers={
            "Content-Type": "application/x-amz-json-1.1",
            "X-Amz-Target": "AWSCognitoIdentityService.GetCredentialsForIdentity",
        },
        data=json.dumps({"IdentityId": identity_id}),
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

    def sign(key, msg):
        if isinstance(msg, str):
            msg = msg.encode("utf-8")
        return hmac.new(key, msg, hashlib.sha256).digest()

    def get_signature_key(key, date_stamp, region_name, service_name):
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
    creds: dict,
    region: str,
    payload_dict: dict,
    signed_headers: str,
    target: str,
) -> dict:
    payload = json.dumps(payload_dict)
    headers = generate_signature_headers(
        payload, creds, region, signed_headers, target
    )

    endpoint = f"https://dynamodb.{region}.amazonaws.com/"
    response = requests.post(endpoint, headers=headers, data=payload)

    if not response.ok:
        print(f"Error: {response.status_code}")
        print(f"Response: {response.text}")

    response.raise_for_status()
    return response.json()
