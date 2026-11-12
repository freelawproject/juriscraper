"""Helpers for scrapers that drive ASP.NET WebForms postbacks."""

import re

from juriscraper.lib.log_tools import make_default_logger

logger = make_default_logger()

WAF_SQLI_HEX_LITERAL_RE = re.compile(r"0(?=[xX][0-9a-fA-F]{3})")

BASE64_STATE_FIELDS = ("__VIEWSTATE", "__EVENTVALIDATION")


def breakup_hex_substrings(form_data: dict[str, str]) -> dict[str, str]:
    """Rewrite a postback body so a WAF's SQLi rules won't reject it.

    An Azure Application Gateway rejects a postback whenever the ViewState it
    echoes back happens to contain an MSSQL hex literal, which it does most of
    the time. A 403 served by "Microsoft-Azure-Application-Gateway/v2" rather
    than by the origin server is that rule firing, not rate limiting.

    Splits the "0x" of every hex-literal run in the Base64 state fields with a
    newline. Base64 decoding ignores whitespace, so the server decodes exactly
    the same bytes and the ViewState MAC still validates, but the signature no
    longer matches.

    Args:
        form_data: The postback body, as a field name -> value mapping.

    Returns:
        A copy of form_data, safe to post.
    """
    defanged = dict(form_data)
    for name, value in defanged.items():
        if name in BASE64_STATE_FIELDS:
            defanged[name] = WAF_SQLI_HEX_LITERAL_RE.sub("0\n", value)
        elif WAF_SQLI_HEX_LITERAL_RE.search(value):
            # A match in any other field is something we can't rewrite
            # without corrupting it. Log it so that an otherwise baffling
            # 403 has a trail.
            logger.warning(
                "Field %s carries a hex literal a WAF may reject: %.80r",
                name,
                value,
            )

    return defanged
