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

import re

from lxml.html import HtmlElement
from typing_extensions import override

from juriscraper.AbstractSite import logger
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
            links = card.xpath(".//a[contains(@href, 'serveFile.php')]")
            title = self._field(card, "Case Title")
            date = self._field(card, "Opinion Filed")
            if not (links and title and date):
                logger.warning(
                    "%s: skipping opinion card missing a PDF link, "
                    "title or filed date: %r",
                    self.court_id,
                    title,
                )
                continue
            summary = card.xpath("string(./div[contains(@class, 'py-20')])")
            self.cases.append(
                {
                    "name": self._case_name(title),
                    "date": date,
                    "docket": links[0].text_content().strip(),
                    "url": links[0].get("href"),
                    "summary": " ".join(summary.split()),
                    "status": "Published",
                }
            )

    @staticmethod
    def _case_name(title: str) -> str:
        """Title case an all caps case title.

        Titles are all caps except the "v." separator and "et al.", and
        titlecase only lowercases strings that are entirely uppercase, so
        each party is cased on its own. titlecase also lowercases a middle
        initial "V.", which would read as a second separator, so restore it.

        :param title: The raw case title, e.g. "JOHN DOE v. JANE V. ROE"
        :return: The title cased case name
        """
        parties = [
            re.sub(r"\bv\.", "V.", titlecase(party.upper()))
            for party in title.split(" v. ")
        ]
        return " v. ".join(parties)

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
