"""Scraper for Connecticut Supreme Court
CourtID: conn
Court Short Name: Conn.
Author: Asadullah Baig <asadullahbeg@outlook.com>
History:
    - 2014-07-11: created
    - 2014-08-08, mlr: updated to fix InsanityError on case_dates
    - 2014-09-18, mlr: updated XPath to fix InsanityError on docket_numbers
    - 2015-06-17, mlr: made it more lenient about date formatting
    - 2016-07-21, arderyp: fixed to handle altered site format
    - 2017-01-10, arderyp: restructured to handle new format use case that includes opinions without dates and flagged for 'future' publication
    - 2022-02-02, satsuki-chan: Fixed docket and name separator, changed super class to OpinionSiteLinear
    - 2023-11-04, flooie: Fix scraper
"""

import re
from datetime import date

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        year = date.today().strftime("%y")
        self.url = (
            f"http://www.jud.ct.gov/external/supapp/archiveAROsup{year}.htm"
        )
        self.status = "Published"
        self.cipher = "AES256-SHA256"
        self.set_custom_adapter(self.cipher)

    @staticmethod
    def find_docket_numbers(text: str) -> str:
        """Find docket numbers in row

        :param text: the row text
        :return: return docket numbers
        """
        matches = re.findall(r"SC\d+", text)
        return ", ".join(matches)

    @staticmethod
    def remove_excess_whitespace(text: str) -> str:
        return re.sub(r"\s+", " ", text)

    @staticmethod
    def find_published_date(row):
        closest_published = row.xpath(
            "preceding::*[contains(., 'Published')][1]"
        )
        date_str = closest_published[0].text_content()
        m = re.search(
            r"(\b\d{1,2}/\d{1,2}/\d{4}\b)|(\b(?:January|February|March|April|May|June|July|August|September|October|November|December) \d{1,2}, \d{4}\b)",
            date_str,
        )
        return m.groups()[0] if m.groups()[0] else m.groups()[1]

    def _process_html(self) -> None:
        """Process the html and extract out the opinions

        :return: None
        """
        pdf_xpath = "//table[@id='AutoNumber1']//a[contains(@href, '.pdf')]"
        for row in self.html.xpath(pdf_xpath):
            url = row.get("href")
            link_text = row.text_content().strip()
            full_row_text = row.getparent().text_content().strip()
            if link_text == full_row_text:
                # Fix for atypical bug found in an older year
                full_row_text = (
                    row.getparent().getparent().text_content().strip()
                )
            docket_with_type_opt = self.remove_excess_whitespace(link_text)
            name = (
                self.remove_excess_whitespace(full_row_text)
                .replace(docket_with_type_opt, "")
                .strip("- ")
            )
            date = self.find_published_date(row)
            dockets = self.find_docket_numbers(docket_with_type_opt)

            self.cases.append(
                {
                    "date": date,
                    "url": url,
                    "docket": dockets,
                    "name": name,
                }
            )
