import unittest

import httpx

from juriscraper.lib.exceptions import (
    BadContentError,
    DownloadStatusError,
    EmptyFileError,
    UnexpectedContentTypeError,
)
from juriscraper.opinions.united_states.administrative_agency import bia, olc
from juriscraper.opinions.united_states.state import mass
from juriscraper.OpinionSite import OpinionSite

URL = "https://court.gov/opinion.pdf"

# Responses a source may serve, as (status, content type, content).
# An Exception instead of a tuple is raised by the transport.
PDF = (200, "application/pdf", b"%PDF-1.7 fake")
EMPTY = (200, "application/pdf", b"")
HTML = (200, "text/html", b"<html>an opinion</html>")
BLOCKED = (403, "text/html", b"<html>blocked by the WAF</html>")
MISSING = (404, "text/html", b"<html>not found</html>")
DROPPED = httpx.ReadError("connection dropped")

# The justice.gov page that `bia` and `olc` read their cookies from
CHALLENGE = b"""<html><script>
let public_salt = "abc123";
let candidates = "one/two".split("/");
</script></html>"""


def _transport(served):
    """Serve `served` in order, repeating the last one once exhausted

    :param served: list of response tuples, or Exceptions to raise
    :return: (transport, calls) where calls is a one-item list of the count
    """
    calls = [0]

    def handler(request: httpx.Request) -> httpx.Response:
        item = served[min(calls[0], len(served) - 1)]
        calls[0] += 1
        if isinstance(item, Exception):
            raise item
        status, content_type, content = item
        return httpx.Response(
            status,
            content=content,
            headers={"Content-Type": content_type},
            request=request,
        )

    return httpx.MockTransport(handler), calls


def _make_site(served, site=None, **attrs):
    """Build a site whose session answers with canned responses

    :param served: what the source serves, see `_transport`
    :param site: the site to equip, an opinion site by default
    :param attrs: attributes to set on the site, such as `retry_codes`
    :return: (site, calls)
    """
    if site is None:
        site = OpinionSite()
        site.court_id = "juriscraper.opinions.united_states.state.test"
    # No wait between attempts, so a retry test does not sleep
    site.backoff = 0
    for name, value in attrs.items():
        setattr(site, name, value)
    # Swap the transport, not the client, so `async with site` still closes
    # the client the site built and the request travels the full httpx path
    site.request["session"]._transport, calls = _transport(served)
    return site, calls


async def _download(site):
    async with site:
        return await site.download_content(URL, doctor_is_available=False)


class DownloadContentTest(unittest.IsolatedAsyncioTestCase):
    """`download_content` checks a response before it returns its content"""

    async def test_response_is_checked_before_its_content_type(self):
        """An error status is reported as such, whatever the body holds"""
        expectations = (
            # served, expected exception, expected status on the exception
            (PDF, None, None),
            (BLOCKED, DownloadStatusError, 403),
            (MISSING, DownloadStatusError, 404),
            (HTML, UnexpectedContentTypeError, None),
            (EMPTY, EmptyFileError, None),
        )
        for served, expected, status in expectations:
            with self.subTest(served=served):
                site, _ = _make_site([served])
                if expected is None:
                    self.assertEqual(await _download(site), served[2])
                    continue
                with self.assertRaises(expected) as cm:
                    await _download(site)
                if status:
                    self.assertEqual(cm.exception.status_code, status)

    async def test_every_failure_is_a_bad_content_error(self):
        """The caller skips one document on these, rather than the court"""
        for served in (BLOCKED, MISSING, HTML, EMPTY):
            with self.subTest(served=served):
                site, _ = _make_site([served])
                with self.assertRaises(BadContentError):
                    await _download(site)


class DownloadRetryTest(unittest.IsolatedAsyncioTestCase):
    """`retry_codes` decides which failures are worth another attempt"""

    async def test_retries(self):
        block_then_pdf = [BLOCKED, PDF]
        drop_then_pdf = [DROPPED, PDF]
        blocks_then_drop = [BLOCKED, BLOCKED, DROPPED]
        expectations = {
            # label: (served, retry_codes, attempts, raises)
            "off by default": ([BLOCKED], set(), 1, DownloadStatusError),
            "recovers": (block_then_pdf, {403}, 2, None),
            "gives up": ([BLOCKED], {403}, 3, DownloadStatusError),
            "listed statuses only": ([MISSING], {403}, 1, DownloadStatusError),
            "a dropped connection too": (drop_then_pdf, {403}, 2, None),
            "no response at all": ([DROPPED], {403}, 3, httpx.ReadError),
            # A response already seen outranks a later dropped connection,
            # so the caller still gets a BadContentError
            "a response outranks a drop": (
                blocks_then_drop,
                {403},
                3,
                DownloadStatusError,
            ),
        }
        for label, (served, codes, attempts, raises) in expectations.items():
            with self.subTest(label):
                site, calls = _make_site(served, retry_codes=codes)
                if raises is None:
                    self.assertEqual(await _download(site), PDF[2])
                else:
                    with self.assertRaises(raises):
                        await _download(site)
                self.assertEqual(calls[0], attempts)

    async def test_max_retries_sets_the_number_of_attempts(self):
        for max_retries, expected_calls in ((0, 1), (1, 2), (3, 4)):
            with self.subTest(max_retries=max_retries):
                site, calls = _make_site(
                    [BLOCKED],
                    retry_codes=frozenset({403}),
                    max_retries=max_retries,
                )
                with self.assertRaises(DownloadStatusError):
                    await _download(site)
                self.assertEqual(calls[0], expected_calls)


class ScraperDownloadConfigTest(unittest.IsolatedAsyncioTestCase):
    """What the scrapers that rely on these checks ask for"""

    def test_mass_retries_the_waf_block(self):
        """mass.gov blocks a share of requests, but not for long. See #2169"""
        self.assertEqual(mass.Site.retry_codes, frozenset({403}))

    async def test_justice_dot_gov_challenge_is_still_solved(self):
        """`bia` and `olc` read the challenge page off the exception

        The status check must not hide that page from them, whichever
        status it arrives with. See #1724
        """
        for module in (bia, olc):
            for status in (200, 403):
                with self.subTest(module=module.__name__, status=status):
                    site, _ = _make_site(
                        [(status, "text/html", CHALLENGE), PDF],
                        site=module.Site(),
                    )
                    self.assertEqual(await _download(site), PDF[2])
                    self.assertIn("authorization_1", site.cookies)

    async def test_a_page_that_is_not_a_challenge_keeps_its_own_error(self):
        """An error page must not be mistaken for the challenge

        Its cookies cannot be read, and the original error has to reach the
        caller as a `BadContentError` so that only this document is skipped.
        """
        for module in (bia, olc):
            for served in (MISSING, (404, "application/pdf", b"%PDF oops")):
                with self.subTest(module=module.__name__, served=served):
                    site, _ = _make_site([served], site=module.Site())
                    with self.assertRaises(BadContentError):
                        await _download(site)


if __name__ == "__main__":
    unittest.main()
