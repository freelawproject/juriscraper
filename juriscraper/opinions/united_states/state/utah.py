import re

from lxml.html import HtmlElement
from typing_extensions import Unpack, override

from juriscraper.AbstractSite import BackscrapeItem, SiteOptions, logger
from juriscraper.lib.string_utils import CaseNameTweaker
from juriscraper.lib.type_utils import ExtractedMetadata
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear[BackscrapeItem]):
    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions[BackscrapeItem]],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.url = "https://legacy.utcourts.gov/opinions/supopin/"
        self.court_id = self.__module__
        self.status = "Published"
        self.should_have_results = True

    @override
    def _process_html(self) -> None:
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        rows: list[HtmlElement] = self.html.xpath(
            "//div[@id='content']//p[a[contains(@href, '.pdf')]]"
        )
        for row in rows:
            texts: list[str] = row.xpath("text()")
            if any("superseded" in t.lower() for t in texts):
                # Superseding opinions are published in their own rows
                logger.info("Skipping row with superseded opinion %s", texts)
                continue

            # pick longest text; if not, HTML comments may cause wrong indexing
            text = sorted(texts)[-1]
            neutral_cite_match = re.search(r"\d{4} UT( App)? \d{1,}", text)
            if neutral_cite_match is None:
                raise ValueError(f"Could not parse opinion citation: {text!r}")
            citation = neutral_cite_match.group(0)

            filed_index = text.find("Filed")
            docket = text[:filed_index].strip(", ")
            date_filed = text[
                filed_index + 5 : neutral_cite_match.start()
            ].strip(" ,")

            self.cases.append(
                {
                    "url": row.findall("a")[0].attrib["href"],
                    "name": row.findall("a")[0].text_content(),
                    "date": date_filed,
                    "citation": citation,
                    "docket": docket,
                }
            )

    @override
    def extract_from_text(self, scraped_text: str) -> ExtractedMetadata:
        """Extract lower court from the scraped text.

        :param scraped_text: The text to extract from.
        :return: A dictionary with the metadata.
        """
        pattern = re.compile(
            r"""
            (On\s+Direct\s+Appeal
                (?:\s+and\s+Petition\s+for\s+Extraordinary\s+Relief)?
            |On\s+Appeal\s+of\s+Interlocutory\s+Order
            |On\s+Certification\s+from\s+the\s+Court\s+of\s+Appeals
            |On\s+Petition\s+for\s+Review\s+ of\s+Agency\s+Decision
            |On\s+Certiorari\s+to\s+the\s+Utah\s+Court\s+of\s+Appeals)

            \s*\n+
            (?P<lower_court>([^\S\r\n]*\S.*(?:\n|$))+?)
            [^\S\r\n]*the\s+Honorable\s+(?P<lower_court_judge>.*?)(\s+No\.)\s*(?P<lower_court_number>\S+)
            """,
            re.MULTILINE | re.VERBOSE | re.IGNORECASE,
        )

        if (match := pattern.search(scraped_text)) is not None:
            lower_court_str = re.sub(
                r"\s+", " ", match.group("lower_court")
            ).strip()
            lower_court_judge = match.group("lower_court_judge").strip()
            lower_court_number = match.group("lower_court_number").strip()

            return {
                "Docket": {
                    "appeal_from_str": lower_court_str,
                },
                "OriginatingCourtInformation": {
                    "assigned_to_str": lower_court_judge,
                    "docket_number": lower_court_number,
                },
            }

        return {}
