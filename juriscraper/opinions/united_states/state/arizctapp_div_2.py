"""
Scraper for Court of Appeals of Arizona, Division 2
CourtID: arizctapp_div_2
Court Short Name: arizctapp_div_2
Author: Andrei Chelaru
Reviewer: mlr
History:
    2014-07-23: Created by Andrei Chelaru
    2021-12-10: URL changed to recent opinions page, satsuki-chan
    2026-10-28: Updated for redesigned recent opinions page. See #2367
"""

from lxml.html import HtmlElement
from typing_extensions import override

from juriscraper.lib.string_utils import titlecase
from juriscraper.opinions.united_states.state import ariz
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    extract_from_text = ariz.Site.extract_from_text

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        # Feeling down and tired of of your regular life? Check out this website.
        self.url = "https://www.appeals2.az.gov/RecentOpinionsHTML.php"
        self.cases = []
        self.should_have_results = True

    @override
    def _process_html(self) -> None:
        """Parse the recent opinions page, where each opinion is a card of
        labelled fields grouped under case-type headings.
        """
        if self.html is None:
            return

        cards = self.html.xpath(
            "//section[@id='allRecentOpinions']"
            "//div[contains(@class, 'gray-border-thick')]"
        )
        for card in cards:
            link = card.xpath(".//a[contains(@href, 'serveFile.php')]")[0]
            summary = card.xpath("string(./div[contains(@class, 'py-20')])")
            # Titles are all caps except "v." and "et al."; titlecase only
            # lowercases strings that are entirely uppercase
            name = self._field(card, "Case Title").upper()
            self.cases.append(
                {
                    "name": titlecase(name),
                    "date": self._field(card, "Opinion Filed"),
                    "docket": link.text_content().strip(),
                    "url": link.get("href"),
                    "summary": " ".join(summary.split()),
                    "status": "Published",
                }
            )

    def _field(self, card: HtmlElement, label: str) -> str:
        """Return the value that follows a "Label: " heading in a card.

        :param card: The opinion card element
        :param label: The field's label, without the trailing colon
        :return: The field's text, or "" if the card has no such field
        """
        # Matching on the label rather than position survives the site
        # reordering fields
        return card.xpath(
            f"string(./div[p[starts-with(normalize-space(), '{label}')]]"
            "/text()[normalize-space()])"
        ).strip()
