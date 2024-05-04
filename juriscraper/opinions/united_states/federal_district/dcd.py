"""Scraper for United States District Court for the District of Columbia
CourtID: dcd
Court Short Name: D.D.C.
Author: V. David Zvenyach
Date created: 2014-02-27
Substantially Revised: Brian W. Carver, 2014-03-28
2024-05-03, grossir: Change base class OpinionSiteLinear
"""

import re
from datetime import date, datetime
from typing import Tuple

from lxml import html

from juriscraper.lib.string_utils import titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    docket_document_number_regex = re.compile(r"(\?)(\d+)([a-z]+)(\d+)(-)(.*)")
    nature_of_suit_regex = re.compile(r"(\?)(\d+)([a-z]+)(\d+)(-)(.*)")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = f"https://ecf.dcd.uscourts.gov/cgi-bin/Opinions.pl?{date.today().year}"
        self.status = "Published"

    def _process_html(self):
        """
        Some rows have mutliple documents and hence urls for each case.
        We will "pad" every other metadata field to match the urls
        """
        for row in self.html.xpath("//table[2]//tr[not(th)]"):
            case_name = titlecase(
                row.xpath("td[2]//text()[preceding-sibling::br]")[0].lower()
            )
            date_string = row.xpath("td[1]/text()")[0]
            date_filed = datetime.strptime(date_string, "%m/%d/%Y")
            docket = row.xpath("td[2]//text()[following-sibling::br]")[0]

            judge_element = row.xpath("td[3]")[0]
            judge_string = html.tostring(
                judge_element, method="text", encoding="unicode"
            )
            judge = re.search(r"(by\s)(.*)", judge_string, re.MULTILINE).group(
                2
            )

            for url in row.xpath("td[3]/a/@href"):
                doc_number, nature_of_suit = self.get_values_from_url(url)
                self.cases.append(
                    {
                        "name": case_name,
                        "date": str(date_filed),
                        "url": url,
                        "docket": docket,
                        "docket_document_numbers": doc_number,
                        "nature_of_suit": nature_of_suit,
                        "judge": judge,
                    }
                )

    def get_values_from_url(self, url: str) -> Tuple[str, str]:
        """Get docket document number and nature_of_suit values from URL

        :param url:
        :return:  docket document number and nature_of_suit
        """
        # In 2012 (and perhaps elsewhere) they have a few weird urls.
        match = self.docket_document_number_regex.search(url)
        if match:
            doc_number = match.group(6)
        else:
            doc_number = url

        nature_of_suit_match = re.search(self.nature_of_suit_regex, url)
        # In 2012 (and perhaps elsewhere) they have a few weird urls.
        if not nature_of_suit_match:
            nature_of_suit = "Unknown"
        else:
            nature_code = nature_of_suit_match.group(3)
            if nature_code == "cv":
                nature_of_suit = "Civil"
            elif nature_code == "cr":
                nature_of_suit = "Criminal"
            # This is a tough call. Magistrate Cases are typically also
            # Criminal or Civil cases, and their docket_number field will
            # reflect this, but they do classify these separately under
            # these 'mj' and 'mc' codes and the first page of these
            #  documents will often refer to them as 'Magistrate Case
            # ####-####' so, we will too.
            elif nature_code == "mj" or "mc":
                nature_of_suit = "Magistrate Case"
            else:
                nature_of_suit = "Unknown"

        return doc_number, nature_of_suit

    def _get_docket_document_numbers(self):
        return [case["docket_document_numbers"] for case in self.cases]

    def _get_nature_of_suit(self):
        return [case["nature_of_suit"] for case in self.cases]
