"""Scraper for Missouri Supreme Court
CourtID: mo
Court Short Name: MO
Author: Ben Cassedy
Date created: 04/27/2014
History:
    - 2022-02-04, satsuki-chan: Fixed error when not found judge and disposition, changed super class to OpinionSiteLinear
"""

from datetime import date
from typing import List, Tuple
from urllib.parse import urlencode

from juriscraper.lib.string_utils import titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.court_slug = "Supreme"
        self.url = self.build_url()
        self.status = "Published"
        self.cases = []

    def build_url(self) -> str:
        """Get court's URL with search parameters
        Sets search parameters values and encodes them to build an URL to the court's web site

        :return: String with court's URL
        """
        params = (
            ("id", "12086"),
            ("date", "all"),
            ("year", f"{date.today().year}"),
            ("dist", f"Opinions {self.court_slug}"),
        )
        url = f"https://www.courts.mo.gov/page.jsp?{urlencode(params)}#all"
        return url

    def _process_html(self) -> None:
        """Process the html and extract out the opinions

        :return: None
        """
        path = "//div[@id='content']/div/form/table/tr/td"
        for date_block in self.html.xpath(path):
            date_string = date_block.xpath("./input/@value")
            if date_string:
                for case_block in date_block.xpath("./table/tr/td"):
                    links = case_block.xpath("./a")
                    first_link_text = links[0].xpath("text()")
                    if (
                        first_link_text
                        and "Orders Pursuant to Rules" in first_link_text[0]
                    ):
                        # File with list of affirmed cases, skip it
                        continue

                    link_index = 1 if len(links) > 1 else 0
                    bolded_text = case_block.xpath("./b")
                    docket = self.sanitize_docket(
                        bolded_text[0].text_content()
                    )
                    text = case_block.xpath("text()")
                    (
                        judge,
                        disposition,
                    ) = self.parse_judge_disposition_from_text(text)

                    self.cases.append(
                        {
                            "date": date_string[0],
                            "docket": docket,
                            "judge": judge,
                            "url": links[link_index].attrib["href"],
                            "name": titlecase(
                                links[link_index].text_content()
                            ),
                            "disposition": disposition,
                        }
                    )

    @staticmethod
    def sanitize_docket(docket: str) -> str:
        """Get list of case's dockets in a single line
        Removes additional text and characters, and joins list of dockets in a single line

        :return: String with cleaned dockets
        """
        for substring in [":", "and", "_", "Consolidated", "(", ")", ","]:
            docket = docket.replace(substring, " ")
        return ", ".join(docket.split())

    @staticmethod
    def parse_judge_disposition_from_text(
        text_raw_list: List[str],
    ) -> Tuple[str, str]:
        """Get case judge and disposition
        Separate and clean text with the judge of the case and case's disposition, if any.

        :return: Tuple with the judge name and case's disposition
        """
        text_clean_list = [
            text.strip() for text in text_raw_list if text.strip()
        ]
        if len(text_clean_list) == 0:
            return "", ""
        elif len(text_clean_list) == 1:
            return text_clean_list[0], ""
        else:
            return text_clean_list[0], text_clean_list[1]
