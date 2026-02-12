"""Scraper for Kentucky Supreme Court
CourtID: ky
Court Short Name: Ky.
Contact: https://courts.ky.gov/aoc/technologyservices/Pages/ContactTS.aspx

History:
    2014-08-07: Created by mlr.
    2014-12-15: Updated to fetch 100 results instead of 30. For reasons unknown
                this returns more recent results, while a smaller value leaves
                out some of the most recent items.
    2016-03-16: Restructured by arderyp to pre-process all data at donwload time
                to work around resources whose case names cannot be fetched to
                to access restrictions.
    2020-08-28: Updated to use new secondary search portal at https://appellatepublic.kycourts.net/
    2024-04-08: Updated to use new opinion search portal, by grossir
    2025-06-31: Added extract_from_text method to get lower court info, luism
"""

import re
from datetime import date, datetime, timedelta
from typing import Optional
from urllib.parse import urlencode

from juriscraper.AbstractSite import logger
from juriscraper.lib.judge_parsers import normalize_judge_string
from juriscraper.lib.string_utils import titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    # Home: https://appellatepublic.kycourts.net/login
    first_opinion_date = datetime(1982, 2, 18).date()
    days_interval = 7  # page size of 25

    api_court = "Kentucky Supreme Court"
    api_url = (
        "https://appellatepublic.kycourts.net/api/api/v1/opinions/search?"
    )
    docket_entry_url = "https://appellatepublic.kycourts.net/api/api/v1/publicaccessdocuments?filter=parentCategory%3Ddocketentries%2CparentID%3D{}"
    pdf_url = "https://appellatepublic.kycourts.net/api/api/v1/publicaccessdocuments/{}/download"

    # Examples: "BY JUDGE EASTON", "BY CHIEF JUSTICE VANMETER AFFIRMING",
    # "BY JUDGE A. JONES"
    judge_regex = r"BY(\sCHIEF)?\s(JUDGE|JUSTICE)\s(?P<judge>(\w\.\s)?\w+)"

    # Examples: "2022-CA-1454, 1456, 1457"
    docket_regex = r"\d{4}-(CA|SC)-\d{4}(,\s?\d{4})*"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.set_url()
        self.make_backscrape_iterable(kwargs)

    def set_url(
        self, start: Optional[date] = None, end: Optional[date] = None
    ) -> None:
        """Sets URL with appropiate query parameters

        :param start: start date
        :param end: end date
        :return None
        """
        if not start:
            end = datetime.now()
            start = end - timedelta(7)

        logger.info("Date range %s %s", start, end)
        params = {
            "queryString": "true",
            "searchFields[0].operation": ">=",
            "searchFields[0].values[0]": start.strftime("%m/%d/%Y"),
            "searchFields[0].indexFieldName": "filedDate",
            "searchFields[1].operation": "<=",
            "searchFields[1].values[0]": end.strftime("%m/%d/%Y"),
            "searchFields[1].indexFieldName": "filedDate",
            "searchFilters[0].operation": "=",
            "searchFilters[0].indexFieldName": "caseHeader.court",
            "searchFilters[0].values[0]": self.api_court,
        }
        self.url = f"{self.api_url}{urlencode(params)}"

    def _process_html(self) -> None:
        """Parse API JSON response into case dictionaries

        :return None
        """
        result_json = self.html

        for result in result_json["resultItems"]:
            case_name = ""
            row = result["rowMap"]
            date_filed = row["filedDate"]
            disposition = row["docketEntryDescription"]
            docket_number = row["caseHeader.caseNumber"]

            if not row["hasDocuments"]:
                logger.info(
                    "Docket %s has no documents, skipping", docket_number
                )
                continue

            # On "PUBLIC OPINIONS IN CONFIDENTIAL CASES", docket numbers
            # and case names are not as expected
            # "2024 CA ADMIN - NON-CONFIDENTIAL OPINION - 002"
            # The proper docket number may be found on the disposition string
            if not re.search(self.docket_regex, docket_number) and (
                docket_match := re.search(self.docket_regex, disposition)
            ):
                docket_number = docket_match.group(0)
                # Delete docket numbers from disposition
                disposition = re.sub(self.docket_regex, "", disposition)
                if "\n" in disposition:
                    disposition, case_name = disposition.split("\n", 1)

            judge = ""
            if judge_match := re.search(self.judge_regex, disposition):
                judge = normalize_judge_string(judge_match.group("judge"))[0]
                # Drop from the disposition everything after "BY JUDGE..."
                # May contain the case name
                disposition = re.split(self.judge_regex, disposition)[0]

            if disposition.upper() in [
                "OPINION OF THE COURT",
                "OPINION AND ORDER",
            ]:
                disposition = ""

            if self.test_mode_enabled():
                # detail request has been manually nested in the test file
                doc_json = result["detailJson"]
            else:
                detail_url = self.docket_entry_url.format(row["docketEntryID"])
                doc_json = self.get_json(detail_url)

            if not doc_json:
                logger.error(
                    "ky: no document details returned for Docket %s",
                    docket_number,
                )
                continue

            if not case_name:
                case_name = doc_json[0]["caseHeader"].get("shortTitle")
            doc_id = doc_json[0].get("documentID")
            doc_text = (
                doc_json[0]["documentText"][0]
                if doc_json[0].get("documentText")
                else ""
            )

            if not doc_text:
                status = "Unknown"
            elif "\r\nTO BE PUBLISHED \r\n" in doc_text:
                status = "Published"
            else:
                status = "Unpublished"

            self.cases.append(
                {
                    "url": self.pdf_url.format(doc_id),
                    "name": titlecase(case_name),
                    "disposition": disposition,
                    "docket": docket_number,
                    "date": date_filed,
                    "status": status,
                    "judge": judge,
                }
            )

    def get_json(self, url: str) -> dict:
        """Get JSON from the API

        :param url: url
        :return: JSON as dict
        """
        logger.debug("Getting JSON: '%s'", url)
        self._request_url_get(url)
        self._post_process_response()
        return self._return_response_text_object()

    def _download_backwards(self, dates: tuple[date, date]) -> None:
        """Set date range from backscraping args and scrape

        :param dates: (start_date, end_date) tuple
        :return None
        """
        logger.info("Backscraping for range %s %s", *dates)
        self.set_url(*dates)
        self.html = self._download()
        self._process_html()

    def extract_from_text(self, scraped_text: str) -> dict:
        """Extract lower court from the scraped text.

        :param scraped_text: The text to extract from.
        :return: A dictionary with the metadata.
        """
        pattern = re.compile(
            r"""
            ON\s+(?:APPEAL|REVIEW)\s+FROM\s+(?P<lower_court>[^\n.]+)
            .*?
            (?:HONORABLE\s+(?P<lower_court_judge>[\w\s.\-]+),\s*JUDGE.*?)?
            NOS?\.\s*(?P<lower_court_number>[\w\-]+)
            """,
            re.I | re.S | re.X,
        )

        result = {}
        if match := pattern.search(scraped_text):
            lower_court = re.sub(
                r"\s+", " ", match.group("lower_court")
            ).strip()

            # Prepend 'Kentucky' if lower_court is 'Court of Appeals'
            if lower_court.lower() == "court of appeals":
                lower_court = "Kentucky Court of Appeals"

            result["Docket"] = {
                "appeal_from_str": titlecase(lower_court),
            }

            lower_court_judge = match.group("lower_court_judge")
            lower_court_number = match.group("lower_court_number")

            if lower_court_judge:
                result.setdefault("OriginatingCourtInformation", {})[
                    "assigned_to_str"
                ] = titlecase(lower_court_judge.strip())
            if lower_court_number:
                result.setdefault("OriginatingCourtInformation", {})[
                    "docket_number"
                ] = lower_court_number.strip()

        return result
