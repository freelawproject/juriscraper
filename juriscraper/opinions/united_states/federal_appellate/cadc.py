"""
CourtID: cadc
Court Short Name: Court of Appeals of the District of Columbia
Author: mlissner
History:
    2014-07-31, mlissner: commited first version
    2024-12-31, grossir: Implemented new site
    2025-08-26, lmanzur: Updated added extract_from_text.
"""

import re

from lxml.html import HtmlElement
from typing_extensions import Unpack, override

from juriscraper.AbstractSite import SiteOptions
from juriscraper.lib.string_utils import CaseNameTweaker, titlecase
from juriscraper.lib.type_utils import ExtractedMetadata
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.court_id = self.__module__
        # https://media.cadc.uscourts.gov/opinions/
        self.url = "https://media.cadc.uscourts.gov/opinions/bydate/recent"
        self.status = "Published"

    @override
    def _process_html(self) -> None:
        link_xpath = "a[contains(@href, '.pdf')]"
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        rows: list[HtmlElement] = self.html.xpath(
            f"//div[div[div[div[{link_xpath}]]]]"
        )
        for row in rows:
            self.cases.append(
                {
                    "url": row.xpath(f".//{link_xpath}/@href")[0],
                    "docket": row.xpath(f".//{link_xpath}/text()")[0],
                    "name": row.xpath("div[2]/div/div/text()")[0],
                    "date": row.xpath(".//span/text()")[-1],
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
            (?:
               (?:On\s+)?Appeals?\s+from\s+the\s+
              | (?:On\s+)?Petitions?\s+for\s+Review\s+of\s+(?:a\s+)?(?:Final\s+)?Action\s+of\s+the\s+
            )
            (?P<lower_court>[^.]+?)
            (?=\s*(?:\.|\(|Nos?\.|USC|D.C.|\n\s*\n))
            """,
            re.X | re.IGNORECASE,
        )

        lower_court = ""
        if (match := pattern.search(scraped_text)) is not None:
            lower_court = re.sub(
                r"\s+", " ", match.group("lower_court")
            ).strip()

        if bool(lower_court):
            return {
                "Docket": {
                    "appeal_from_str": titlecase(lower_court),
                }
            }

        return {}
