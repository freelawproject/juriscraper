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
from typing import Tuple

from dateutil.parser import parse

from juriscraper.AbstractSite import logger
from juriscraper.lib.string_utils import clean_string
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    court_abbv = "sup"
    start_year = 2000
    base_url = "http://www.jud.ct.gov/external/supapp/archiveARO{}{}.htm"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.status = "Published"

        self.current_year = int(date.today().strftime("%Y"))
        self.url = self.make_url(self.current_year)
        self.make_backscrape_iterable(kwargs)

        self.cipher = "AES256-SHA256"
        self.set_custom_adapter(self.cipher)

    @staticmethod
    def find_published_date(date_str: str) -> str:
        """Extract published date

        :param date_str: The row text
        :return: The date string
        """
        m = re.search(
            r"(\b\d{1,2}/\d{1,2}/\d{2,4}\b)|(\b(?:January|February|March|April|May|June|July|August|September|October|November|December) \d{1,2}, \d{4}\b)",
            date_str,
        )
        return m.groups()[0] if m.groups()[0] else m.groups()[1]

    def extract_dockets_and_name(self, row) -> Tuple[str, str]:
        """Extract the docket and case name from each row

        :param row: Row to process
        :return: Docket(s) and Case Name
        """
        text = " ".join(row.xpath("ancestor::li[1]//text()"))
        clean_text = re.sub(r"[\n\r\t\s]+", " ", text)
        m = re.match(
            r"(?P<dockets>[SAC0-9, ]+)(?P<op_type> [A-Z].*)? - (?P<case_name>.*)",
            clean_text,
        )
        if not m:
            # Handle bad inputs
            m = re.match(
                r"(?P<dockets>[SAC0-9, ]+)(?P<op_type> [A-Z].*)? (?P<case_name>.*)",
                clean_text,
            )
        op_type = m.group("op_type")
        name = m.group("case_name")
        if op_type:
            name = f"{name} ({op_type.strip()})"
        return m.group("dockets"), name

    def _process_html(self) -> None:
        """Process the html and extract out the opinions

        :return: None
        """
        for row in self.html.xpath(".//*[contains(@href, '.pdf')]"):
            pub = row.xpath('preceding::*[contains(., "Published")][1]/text()')
            if pub:
                date_filed_is_approximate = False
                date_filed = self.find_published_date(pub[0])
            else:
                # May happen on most recent opinions, which have a header like
                # "Publication in the Connecticut Law Journal To Be Determined"
                date_filed = f"{self.current_year}-07-01"
                date_filed_is_approximate = True

            dockets, name = self.extract_dockets_and_name(row)
            self.cases.append(
                {
                    "url": row.get("href"),
                    "name": name,
                    "docket": dockets,
                    "date": date_filed,
                    "date_filed_is_approximate": date_filed_is_approximate,
                }
            )

    def make_url(self, year: int) -> str:
        """Makes URL using year input
        Data available since 2000, so (year % 2000) will work fine

        :param year: full year integer
        :return: url
        """
        year_str = str(year % 2000).zfill(2)
        return self.base_url.format(self.court_abbv, year_str)

    def extract_from_text(self, scraped_text: str):
        """
        If possible, extract Opinion Cluster values:
            - date_filed
            - procedural_history
            - syllabus
            - judges

        :param scraped_text: Text extracted from the PDF
        :returns: metadata object expected by Courtlistener
        """
        metadata = {"OpinionCluster": {}}

        # initial value for end index for judges
        judges_end = 1_000_000

        # it may not exist on secondary opinions, like a Dissent attached to the
        # main cluster
        regex_date = r"Argued.+officially\sreleased\s(?P<date>[JFMASOND]\w+\s\d{1,2},\s\d{4})"
        if date_match := re.search(regex_date, scraped_text):
            try:
                date_filed = parse(date_match.group("date")).date()
                metadata["OpinionCluster"].update(
                    {
                        "date_filed": date_filed,
                        "date_filed_is_approximate": False,
                    }
                )
            except ValueError:
                pass

            judges_end = date_match.start()

        # procedural history seems to always exists
        # It ends when the Opinion begins
        ph_start_index = scraped_text.find("Procedural History")
        if ph_start_index != -1:
            end_index = scraped_text.find("Opinion", ph_start_index)
            if end_index != -1:
                procedural_history = scraped_text[
                    ph_start_index + 18 : end_index
                ]
                metadata["OpinionCluster"]["procedural_history"] = (
                    clean_extracted_text(procedural_history)
                )

            judges_end = min(judges_end, ph_start_index)

        # sometimes the syllabus does not exist
        # If it does, it is before the Procedural History
        sy_start_index = scraped_text.find("Syllabus")
        if sy_start_index != -1:
            if ph_start_index:
                syllabus = scraped_text[sy_start_index + 8 : ph_start_index]
                metadata["OpinionCluster"]["syllabus"] = clean_extracted_text(
                    syllabus
                )

            judges_end = min(judges_end, sy_start_index)

        # Judges string is in the first page after the docket number,
        # before the following section, which may be Syllabus or Procedural History
        if judges_end != 1_000_000:
            if docket_match := list(
                re.finditer(r"[AS]C\s\d{5}", scraped_text[:judges_end])
            ):
                judges = scraped_text[docket_match[-1].end() : judges_end]
                clean_judges = []
                for judge in (
                    judges.strip("\n )(").replace(" and ", ",").split(",")
                ):
                    if not judge.strip() or "Js." in judge or "C. J." in judge:
                        continue
                    clean_judges.append(judge.strip("\n "))

                metadata["OpinionCluster"]["judges"] = "; ".join(clean_judges)

        return metadata

    def _download_backwards(self, year: int) -> None:
        """Build URL with year input and scrape

        :param year: year to scrape
        :return None
        """
        logger.info("Backscraping for year %s", year)
        self.url = self.make_url(year)
        self.html = self._download()
        self._process_html()

    def make_backscrape_iterable(self, kwargs: dict) -> None:
        """Checks if backscrape start and end arguments have been passed
        by caller, and parses them accordingly
        :param kwargs: passed when initializing the scraper, may or
            may not contain backscrape controlling arguments
        :return None
        """
        start = kwargs.get("backscrape_start")
        end = kwargs.get("backscrape_end")

        start = int(start) if start else self.start_year
        end = int(end) + 1 if end else self.current_year

        self.back_scrape_iterable = range(start, end)


def clean_extracted_text(text: str) -> str:
    """
    Get rid of page numbers, page headers and case name

    :param: scraped_text
    :return: clean text
    """
    clean_lines = []
    skip_next_line = False
    for line in text.split("\n"):
        if skip_next_line:
            skip_next_line = False
            continue
        if re.search(r"CONNECTICUT LAW JOURNAL|0\sConn\.\s(App\.\s)?1", line):
            skip_next_line = True
            # following line for one of these regexes is the case name
            continue

        clean_lines.append(line)
    return clean_string("\n".join(clean_lines))
