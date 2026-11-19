"""Scraper for the Kansas Attorney General
CourtID: kanag
Court Short Name: Kansas Attorney General

History:
    - 2026-11-19: created. The source is the Washburn University School of Law
      archive (1974 to present); the Kansas AG website only has recent years
"""

import re
import ssl
from datetime import date
from typing import Any
from urllib.parse import urlparse

import certifi
from dateutil import parser
from typing_extensions import override

from juriscraper.lib.log_tools import make_default_logger
from juriscraper.OpinionSite import ExtractedMetaData
from juriscraper.OpinionSiteLinear import OpinionSiteLinear

logger = make_default_logger()

# The Washburn server does not send its intermediate certificate, so
# verification fails with "unable to get local issuer certificate". Browsers
# fetch the missing certificate on their own; we embed it instead of
# disabling verification. It is a public certificate, valid until 2031-03-29
# Source: http://cacerts.digicert.com/DigiCertGlobalG2TLSRSASHA2562020CA1-1.crt
DIGICERT_G2_TLS_RSA_SHA256_2020_CA1 = """-----BEGIN CERTIFICATE-----
MIIEyDCCA7CgAwIBAgIQDPW9BitWAvR6uFAsI8zwZjANBgkqhkiG9w0BAQsFADBh
MQswCQYDVQQGEwJVUzEVMBMGA1UEChMMRGlnaUNlcnQgSW5jMRkwFwYDVQQLExB3
d3cuZGlnaWNlcnQuY29tMSAwHgYDVQQDExdEaWdpQ2VydCBHbG9iYWwgUm9vdCBH
MjAeFw0yMTAzMzAwMDAwMDBaFw0zMTAzMjkyMzU5NTlaMFkxCzAJBgNVBAYTAlVT
MRUwEwYDVQQKEwxEaWdpQ2VydCBJbmMxMzAxBgNVBAMTKkRpZ2lDZXJ0IEdsb2Jh
bCBHMiBUTFMgUlNBIFNIQTI1NiAyMDIwIENBMTCCASIwDQYJKoZIhvcNAQEBBQAD
ggEPADCCAQoCggEBAMz3EGJPprtjb+2QUlbFbSd7ehJWivH0+dbn4Y+9lavyYEEV
cNsSAPonCrVXOFt9slGTcZUOakGUWzUb+nv6u8W+JDD+Vu/E832X4xT1FE3LpxDy
FuqrIvAxIhFhaZAmunjZlx/jfWardUSVc8is/+9dCopZQ+GssjoP80j812s3wWPc
3kbW20X+fSP9kOhRBx5Ro1/tSUZUfyyIxfQTnJcVPAPooTncaQwywa8WV0yUR0J8
osicfebUTVSvQpmowQTCd5zWSOTOEeAqgJnwQ3DPP3Zr0UxJqyRewg2C/Uaoq2yT
zGJSQnWS+Jr6Xl6ysGHlHx+5fwmY6D36g39HaaECAwEAAaOCAYIwggF+MBIGA1Ud
EwEB/wQIMAYBAf8CAQAwHQYDVR0OBBYEFHSFgMBmx9833s+9KTeqAx2+7c0XMB8G
A1UdIwQYMBaAFE4iVCAYlebjbuYP+vq5Eu0GF485MA4GA1UdDwEB/wQEAwIBhjAd
BgNVHSUEFjAUBggrBgEFBQcDAQYIKwYBBQUHAwIwdgYIKwYBBQUHAQEEajBoMCQG
CCsGAQUFBzABhhhodHRwOi8vb2NzcC5kaWdpY2VydC5jb20wQAYIKwYBBQUHMAKG
NGh0dHA6Ly9jYWNlcnRzLmRpZ2ljZXJ0LmNvbS9EaWdpQ2VydEdsb2JhbFJvb3RH
Mi5jcnQwQgYDVR0fBDswOTA3oDWgM4YxaHR0cDovL2NybDMuZGlnaWNlcnQuY29t
L0RpZ2lDZXJ0R2xvYmFsUm9vdEcyLmNybDA9BgNVHSAENjA0MAsGCWCGSAGG/WwC
ATAHBgVngQwBATAIBgZngQwBAgEwCAYGZ4EMAQICMAgGBmeBDAECAzANBgkqhkiG
9w0BAQsFAAOCAQEAkPFwyyiXaZd8dP3A+iZ7U6utzWX9upwGnIrXWkOH7U1MVl+t
wcW1BSAuWdH/SvWgKtiwla3JLko716f2b4gp/DA/JIS7w7d7kwcsr4drdjPtAFVS
slme5LnQ89/nD/7d+MS5EHKBCQRfz5eeLjJ1js+aWNJXMX43AYGyZm0pGrFmCW3R
bpD0ufovARTFXFZkAdl9h6g4U5+LXUZtXMYnhIHUfoyMo5tS58aI7Dd8KvvwVVo4
chDYABPPTHPbqjc1qCmBaZx2vN4Ye5DUys/vZwP9BFohFrH/6j/f3IL16/RZkiMN
JCqVJUzKoZHm1Lesh3Sz8W2jmdv51b2EQJ8HmA==
-----END CERTIFICATE-----
"""


class Site(OpinionSiteLinear):
    base_url = "https://ksag.washburnlaw.edu/opinions"
    first_year = 1974

    def __init__(self, *args, **kwargs):
        ctx = ssl.create_default_context(cafile=certifi.where())
        ctx.load_verify_locations(cadata=DIGICERT_G2_TLS_RSA_SHA256_2020_CA1)
        kwargs.setdefault("verify", ctx)
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.status = "Published"
        self.year = date.today().year
        self.url = f"{self.base_url}/{self.year}/"

    @override
    async def _download(self, request_dict: dict | None = None) -> Any:
        """Download the current year page

        In January, also download the previous year page, to not miss
        opinions issued in late December and posted late

        :param request_dict: passed to the parent method
        :return: the current year page
        """
        html = await super()._download(request_dict)
        today = date.today()
        if self.test_mode_enabled() or today.month != 1:
            return html
        if self.url != f"{self.base_url}/{today.year}/":
            return html

        current_url = self.url
        previous_year = today.year - 1
        self.url = f"{self.base_url}/{previous_year}/"
        try:
            previous_html = await super()._download(request_dict)
            self._parse_year_page(previous_html, previous_year)
        finally:
            self.url = current_url
        return html

    @override
    def _process_html(self) -> None:
        """Parse the year page

        :return: None
        """
        # Prefer the year in the page's heading over the one in the URL, which
        # may not be the one that was actually downloaded (e.g. test mode)
        if self.html is None:
            return
        heading = " ".join(self.html.xpath("//h1//text()"))
        if match := re.search(r"\b(\d{4})\b", heading):
            page_year = match.group(1)
        else:
            page_year = self.url.rstrip("/").rsplit("/", 1)[-1]
        self._parse_year_page(self.html, page_year)

    def _parse_year_page(self, html: Any, page_year: int | str) -> None:
        """Parse a year page: a list of links to each opinion

        Links are taken as they are on the page since file names are
        irregular (e.g. `2012-005a.pdf`). Some year pages carry links that
        belong to another year, which are broken; those are skipped.

        :param html: the parsed year page
        :param page_year: the year of the page
        :return: None
        """
        for link in html.xpath("//p[@id='listofopinions']//a[@href]"):
            href = link.get("href")
            # The tree may already have absolute links; use the file name
            filename = urlparse(href).path.rsplit("/", 1)[-1]
            docket = filename.rsplit(".", 1)[0]
            url = f"{self.base_url}/{page_year}/{filename}"
            if not docket.startswith(f"{page_year}-"):
                logger.warning(
                    "kanag: skipping link %s on the %s page", href, page_year
                )
                continue

            self.cases.append(
                {
                    "url": url,
                    "docket": docket,
                    "name": f"Kansas Attorney General Opinion {docket}",
                    # The year page has no dates; the real one is extracted
                    # from the opinion text
                    "date": f"{page_year}-07-01",
                    "date_filed_is_approximate": True,
                }
            )

    @override
    def extract_from_text(self, scraped_text: str) -> ExtractedMetaData:
        """Extract the exact date, synopsis and Attorney General's name

        The text starts with the date, followed by
        `ATTORNEY GENERAL OPINION NO. 2026-12`; the number is not reliable
        (not zero padded, spaces), so it is not used

        :param scraped_text: text of the opinion, from a PDF or an htm file
        :return: the extracted metadata
        """
        cluster: dict = {}

        # Search for the date only at the start of the text
        header = scraped_text[:1500]
        date_match = re.search(
            r"([A-Z][a-z]+\.? +\d{1,2}, *\d{4})\s+ATTORNEY\s+GENERAL\s+OPINION",
            header,
        ) or re.search(r"([A-Z][a-z]+\.? +\d{1,2}, *\d{4})", header)
        if date_match:
            try:
                cluster["date_filed"] = parser.parse(
                    date_match.group(1)
                ).strftime("%Y-%m-%d")
                cluster["date_filed_is_approximate"] = False
            except (ValueError, OverflowError):
                pass

        if synopsis := re.search(
            r"Synopsis:\s*(.+?)\n\s*\*\s+\*(?:\s+\*)?\s*\n",
            scraped_text,
            re.DOTALL,
        ):
            cluster["summary"] = " ".join(synopsis.group(1).split())

        # The name goes right above "Attorney General" in the signature
        signature = re.search(
            r"(?:Sincerely|Very\s+truly\s+yours),?(.*)",
            scraped_text,
            re.DOTALL,
        )
        name = signature and re.search(
            r"([^\n/]*[A-Za-z][^\n]*?)\s*\n\s*Attorney\s+General\b",
            signature.group(1),
        )
        if name:
            judge = re.sub(r"^/s/\s*", "", name.group(1).strip())
            cluster["judges"] = judge.title() if judge.isupper() else judge

        if cluster:
            return {"OpinionCluster": cluster}
        return {}

    async def _download_backwards(self, year: int) -> None:
        """Download the page of a given year

        :param year: the year to scrape
        :return: None
        """
        logger.info("Backscraping for year %s", year)
        self.url = f"{self.base_url}/{year}/"
        self.html = await self._download()
        self._process_html()

    @override
    def make_backscrape_iterable(self, kwargs: dict) -> None:
        """Make an iterable of years, one page per year

        :param kwargs: may contain `backscrape_start` and `backscrape_end`
            as years
        :return: None
        """
        start = kwargs.get("backscrape_start")
        end = kwargs.get("backscrape_end")
        start = int(start) if start else self.first_year
        end = int(end) if end else self.year
        self.back_scrape_iterable = range(start, end + 1)
