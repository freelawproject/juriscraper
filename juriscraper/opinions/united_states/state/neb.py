import re

from lxml.html import HtmlElement
from typing_extensions import Unpack, override

from juriscraper.AbstractSite import SiteOptions, logger
from juriscraper.lib.html_utils import fix_links_in_lxml_tree
from juriscraper.lib.string_utils import CaseNameTweaker, titlecase
from juriscraper.lib.type_utils import ExtractedMetadata
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    citation_regex = re.compile(
        r"Cite\s+as\s+(?P<citation>\d+ +Neb\.( App\.)? \d+)"
    )

    lower_court_regex = re.compile(
        r"""
                    Appeals?\s+from\s+the\s+
                    (?P<lower_court>.*?):\s+(?P<judge>.+?),\s*Judge
                    """,
        re.X | re.DOTALL,
    )

    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.court_id = self.__module__
        self.url = (
            "https://supremecourt.nebraska.gov/courts/supreme-court/opinions"
        )
        self.should_have_results = True

    @override
    def _return_response_text_object(self) -> HtmlElement | None:
        """Remove faulty URLs from HTML

        Override _return_response_text_object in Abstract Site to remove any
        url to [site:url-brief] which causes lxml/ipaddress to explode.

        This bug only exists in 3.11 and 3.12

        <a href="https://[site:url-brief]/node/19063" ... >District Map</a>

        :return: The cleaned html tree of the site
        """
        if "response" in self.request:
            response = self.request.get("response")
            if response is None:
                raise ValueError("Download a response before accessing it.")
            payload = response.text
            text = self._clean_text(payload)
            html_tree = self._make_html_tree(text)

            tags: list[HtmlElement] = html_tree.xpath(
                "//a[contains(@href, 'site:url-brief')]"
            )
            for tag in tags:
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
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        for table in self.html.findall(".//table"):
            date_tags: list[str] = table.xpath("preceding::time[1]/text()")
            if not bool(date_tags):
                continue
            date = date_tags[0]

            for row in table.findall(".//tr[td]"):
                c1, c2, c3 = row.findall(".//td")
                docket: str = c1.xpath(".//text()")[0].strip()
                if "A-XX-XXXX" in docket or not bool(c3.findall(".//a")):
                    logger.info("Skip row %s", row.text_content())
                    continue

                citation: str = c2.xpath(".//text()")[0].strip()
                name: str = c3.xpath(".//a/text()")[0].strip()
                url = c3.findall(".//a")[0].attrib["href"]
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
    def extract_from_text(self, scraped_text: str) -> ExtractedMetadata:
        """Get the state citation and lower court info from the document's text."""
        result: ExtractedMetadata = {}

        match = self.citation_regex.search(scraped_text[:1000])
        if match is not None:
            result["Citation"] = match.group("citation")

        match = self.lower_court_regex.search(scraped_text)
        if match is not None:
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
