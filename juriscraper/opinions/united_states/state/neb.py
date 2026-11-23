"""Scraper for the Nebraska Supreme Court
CourtID: neb
Court Short Name: Neb.
History:
 - 2026-11-23: backscraper over the Nebraska Appellate Courts Online Library
"""

import re
from datetime import date, datetime

import httpx
from typing_extensions import override

from juriscraper.AbstractSite import UnexpectedRequestResponseException, logger
from juriscraper.lib.html_utils import fix_links_in_lxml_tree
from juriscraper.lib.string_utils import titlecase
from juriscraper.OpinionSite import ExtractedMetaData
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    citation_regex = re.compile(
        r"Cite\s+as\s+(?P<citation>\d+ +Neb\.( App\.)? \d+)"
    )

    # Parallel citation printed on its own line under the caption of
    # certified opinions, right above the "Filed" line. Anchoring on that
    # layout matters: older PDFs start with the last page of the previous
    # opinion, which may cite other cases. Advance sheets have a
    # "___ N.W.3d ___" placeholder, which won't match
    parallel_citation_regex = re.compile(
        r"^\s*(?P<citation>\d+ +N\.W\.(?:2d|3d) +\d+)\s*\n\s*Filed\s",
        re.MULTILINE,
    )

    # The Online Library lists every opinion of the bound volumes it holds.
    # Volumes are paginated, most recent first. Older volumes are only
    # available as a single PDF, and can't be backscraped
    backscrape_url = "https://www.nebraska.gov/apps-courts-epub/public/supreme"
    volumes_per_page = 25
    # opening date of 275 Neb., first volume with an opinions list
    first_opinion_date = date(2008, 2, 8)

    lower_court_regex = re.compile(
        r"""
                    Appeals?\s+from\s+the\s+
                    (?P<lower_court>.*?):\s+(?P<judge>.+?),\s*Judge
                    """,
        re.X | re.DOTALL,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = (
            "https://supremecourt.nebraska.gov/courts/supreme-court/opinions"
        )
        self.should_have_results = True
        self.make_backscrape_iterable(kwargs)

    def _return_response_text_object(self):
        """Remove faulty URLs from HTML

        Override _return_response_text_object in Abstract Site to remove any
        url to [site:url-brief] which causes lxml/ipaddress to explode.

        This bug only exists in 3.11 and 3.12

        <a href="https://[site:url-brief]/node/19063" ... >District Map</a>

        :return: The cleaned html tree of the site
        """
        if self.request["response"]:
            if not isinstance(self.request["response"], httpx.Response):
                raise UnexpectedRequestResponseException
            payload = self.request["response"].text
            text = self._clean_text(payload)
            html_tree = self._make_html_tree(text)

            for tag in html_tree.xpath(
                "//a[contains(@href, 'site:url-brief')]"
            ):
                parent = tag.getparent()
                if parent is not None:
                    parent.remove(tag)

            if hasattr(html_tree, "rewrite_links"):
                html_tree.rewrite_links(
                    fix_links_in_lxml_tree, base_href=self.request["url"]
                )
            return html_tree

    @override
    def _process_html(self) -> None:
        for table in self.html.xpath(".//table"):
            date_tags = table.xpath("preceding::time[1]/text()")
            if not date_tags:
                continue
            date = date_tags[0]

            for row in table.xpath(".//tr[td]"):
                c1, c2, c3 = row.xpath(".//td")
                docket = c1.xpath(".//text()")[0].strip()
                if "A-XX-XXXX" in docket or not c3.xpath(".//a"):
                    logger.info("Skip row %s", row.text_content())
                    continue

                citation = c2.xpath(".//text()")[0].strip()
                name = c3.xpath(".//a/text()")[0].strip()
                url = c3.xpath(".//a")[0].get("href")
                # This URL location is used for unpublished opinions
                if "/sites/default/files" in url:
                    status = "Unpublished"
                else:
                    status = "Published"

                self.cases.append(
                    {
                        "date": date,
                        "docket": docket,
                        "name": name,
                        "citation": citation,
                        "url": url,
                        "status": status,
                    }
                )

    @override
    def make_backscrape_iterable(self, kwargs: dict) -> None:
        """Build a single (start, end) date tuple

        The source can't be queried by date, so a single element is used to
        walk the volume pages only once

        :param kwargs: may contain `backscrape_start` and `backscrape_end`
            in "%Y/%m/%d" format. Defaults to all the available volumes
        :return: None; sets self.back_scrape_iterable in place
        """
        start = kwargs.get("backscrape_start")
        end = kwargs.get("backscrape_end")

        start = (
            datetime.strptime(start, "%Y/%m/%d").date()
            if start
            else self.first_opinion_date
        )
        end = (
            datetime.strptime(end, "%Y/%m/%d").date() if end else date.today()
        )
        self.back_scrape_iterable = [(start, end)]

    @override
    async def _download_backwards(self, dates: tuple[date, date]) -> None:
        """Walk the volume pages collecting the opinions filed in the range

        :param dates: (start, end) tuple, both inclusive
        :return: None
        """
        start, end = dates
        logger.info("Backscraping for range %s %s", start, end)

        offset = 0
        while True:
            self.url = (
                f"{self.backscrape_url}?offset={offset}"
                f"&max={self.volumes_per_page}"
            )
            self.html = await self._download()
            if not self._process_backscrape_html(start, end):
                break
            offset += self.volumes_per_page

    def _process_backscrape_html(self, start: date, end: date) -> bool:
        """Parse a page of volumes of the Online Library

        :param start: first filing date to collect
        :param end: last filing date to collect
        :return: True if older volumes on the next page may be in the range
        """
        html = self.html
        if html is None:
            return False

        has_opinions = False
        oldest_opening = None

        for volume in html.xpath("//div[contains(@class, 'volume-item')]"):
            header = volume.xpath("./div[contains(@class, 'row')]/div")
            volume_name = " ".join(header[0].text_content().split())
            # "06/22/2012 - 01/10/2013"; the current volume has no closing date
            opening = re.search(r"\d{2}/\d{2}/\d{4}", header[2].text_content())
            if opening:
                oldest_opening = datetime.strptime(
                    opening.group(0), "%m/%d/%Y"
                ).date()

            rows = volume.xpath(".//table/tbody/tr[td]")
            if not rows:
                logger.info("No opinions list for volume %s", volume_name)
                continue
            has_opinions = True

            count = len(self.cases)
            for row in rows:
                c_date, c_docket, c_name, c_citation, c_link = row.xpath("td")
                date_filed = c_date.text_content().strip()
                filed = datetime.strptime(date_filed, "%m/%d/%Y").date()
                if not start <= filed <= end:
                    continue

                urls = c_link.xpath(".//a/@href")
                if not urls:
                    logger.info("Skip row %s", row.text_content())
                    continue

                # consolidated cases have a docket number per line
                dockets = [
                    d.strip() for d in c_docket.xpath(".//text()") if d.strip()
                ]
                self.cases.append(
                    {
                        "date": date_filed,
                        "docket": ", ".join(dockets),
                        "name": " ".join(c_name.text_content().split()),
                        "citation": " ".join(
                            c_citation.text_content().split()
                        ),
                        "url": urls[0],
                        "status": "Published",
                    }
                )
            if len(self.cases) > count:
                logger.info(
                    "Volume %s: %s opinions in range",
                    volume_name,
                    len(self.cases) - count,
                )

        has_next_page = bool(html.xpath("//a[@class='nextLink']"))
        return bool(
            has_opinions
            and has_next_page
            and oldest_opening
            and oldest_opening > start
        )

    @override
    def extract_from_text(self, scraped_text: str) -> ExtractedMetaData:
        """Get the citation and lower court info from the document's text.

        The listings already have the state citation, so the regional
        reporter one is preferred when the document has it
        """
        result: ExtractedMetaData = {}

        if match := self.parallel_citation_regex.search(scraped_text[:10000]):
            result["Citation"] = re.sub(r"\s+", " ", match.group("citation"))
        elif match := self.citation_regex.search(scraped_text[:1000]):
            result["Citation"] = match.group("citation")

        match = self.lower_court_regex.search(scraped_text)
        if match:
            result["Docket"] = {
                "appeal_from_str": re.sub(
                    r"\s+", " ", match.group("lower_court")
                ).strip()
            }
            result["OriginatingCourtInformation"] = {
                "assigned_to_str": titlecase(
                    re.sub(r"\s+", " ", match.group("judge")).strip()
                )
            }

        return result
