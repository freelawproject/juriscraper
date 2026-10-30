"""Detect bot-management challenge pages served instead of court content"""

from urllib.parse import urlparse

from juriscraper.lib.exceptions import BotChallengeError, attach_error_context

# (vendor, marker). Markers that vendors also inject into proxied pages,
# such as "/cdn-cgi/challenge-platform/" or "_Incapsula_Resource", must
# stay out of this list.
CHALLENGE_MARKERS = (
    ("cloudflare", "<title>Just a moment...</title>"),
    ("cloudflare", "Attention Required! | Cloudflare"),
    ("cloudflare", "cf-browser-verification"),
    ("cloudflare", "window._cf_chl_opt"),
    ("imperva", "Incapsula incident ID"),
    ("imperva", "Request unsuccessful. Incapsula"),
    ("radware", "Bot Manager Captcha"),
    ("radware", "Radware Bot Manager"),
)

# challenge pages are small, real documents can be large
INSPECTED_BYTES = 65536


def detect_bot_challenge(body: bytes | str, headers=None) -> str | None:
    """Return the vendor name when `body` is a challenge page, else None"""
    if (
        headers is not None
        and str(headers.get("cf-mitigated", "")).lower() == "challenge"
    ):
        return "cloudflare"

    text = body[:INSPECTED_BYTES]
    if isinstance(text, bytes):
        text = text.decode("utf-8", errors="ignore")
    for vendor, marker in CHALLENGE_MARKERS:
        if marker in text:
            return vendor
    return None


def bot_challenge_error(
    message: str, url: str | None, court_id: str | None = None
) -> BotChallengeError:
    """Build a `BotChallengeError` grouped by host in Sentry"""
    host = urlparse(url or "").netloc or "unknown"
    exc = BotChallengeError(message, fingerprint=[host, "bot-challenge"])
    attach_error_context(exc, court_id=court_id, url=url, owner="court-site")
    return exc


def raise_if_bot_challenge(
    body: bytes | str,
    url: str | None,
    court_id: str | None = None,
    headers=None,
) -> None:
    """Raise `BotChallengeError` when `body` is a challenge page"""
    vendor = detect_bot_challenge(body, headers)
    if vendor is None:
        return
    raise bot_challenge_error(
        f"{court_id}: {vendor} bot challenge served instead of {url}",
        url,
        court_id,
    )
