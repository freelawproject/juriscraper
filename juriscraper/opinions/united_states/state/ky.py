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
"""

from datetime import date, datetime, timedelta
from typing import Dict, Optional, Tuple
from urllib.parse import urlencode

from juriscraper.AbstractSite import logger
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    api_court = "Kentucky Supreme Court"
    api_url = (
        "https://appellatepublic.kycourts.net/api/api/v1/opinions/search?"
    )
    api_docket_entry_url = "https://appellatepublic.kycourts.net/api/api/v1/publicaccessdocuments?filter=parentCategory%3Ddocketentries%2CparentID%3D{}"
    api_document_url = (
        "https://appellatepublic.kycourts.net/documents/{}/download"
    )
    api_case_url = "https://appellatepublic.kycourts.net/api/api/v1/cases/{}"
    first_opinion_date = ""

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
            start = end - timedelta(30)

        params = {
            "queryString": "true",
            "searchFields[0].operation": ">=",
            "searchFields[0].values[0]": start.strftime("%m/%d/%Y"),
            "searchFields[0].indexFieldName": "filedDate",
            "searchFields[1].operation": "<=",
            "searchFields[1].values[0]": end.strftime("%m/%d/%Y"),
            "searchFields[1].indexFieldName": "filedDate",
            "searchFilters[0].indexFieldName": "caseHeader.court",
            "searchFilters[0].operation": "=",
            "searchFilters[0].values[0]": self.api_court,
        }
        self.url = f"{self.api_url}{urlencode(params)}"

    def _process_html(self) -> None:
        """Parse HTMl into case dicts

        :return None
        """
        json = self.html

        for result in json["resultItems"]:
            result = result["rowMap"]
            docket_number = result["caseHeader.caseNumber"]
            disposition = result["docketEntryDescription"]
            status = self.get_status(result["docketEntrySubtype"])
            date_filed = result["filedDate"]

            # Doing 2 extra requests. However we could extract
            # the case name from the opinion's text, which is sent
            # already extracted from the server when querying the docket
            # entry documents
            if self.test_mode_enabled():
                url = "placeholder"
                case_name = "placeholder"
            else:
                url = self.get_opinion_url(result["docketEntryID"])
                case_name = self.get_case_name(result["caseHeader.caseID"])

            self.cases.append(
                {
                    "url": url,
                    "name": case_name,
                    "disposition": disposition,
                    "status": status,
                    "docket": docket_number,
                    "date": date_filed,
                }
            )

    def get_opinion_url(self, docket_entry_id: str) -> str:
        """Builds opinion URL using document id from docket entry detail page

        :param docket_entry_id:

        :return: opinion url
        """
        docket_entry_url = self.api_docket_entry_url.format(docket_entry_id)
        doc_json = self.get_json(docket_entry_url)

        if doc_json and doc_json[0].get("documentID"):
            url = self.api_document_url.format(doc_json[0]["documentID"])
        else:
            url = ""
            logger.info("No docket entry documents found %s", docket_entry_url)

        return url

    def get_case_name(self, case_id: str) -> str:
        """Get case name from case page

        :param case_id: case id
        :return: case name
        """
        case_url = self.api_case_url.format(case_id)
        case_json = self.get_json(case_url)
        return case_json["shortTitle"]

    def get_json(self, url: str) -> Dict:
        """Get JSON from the API

        :param url: url
        :return: JSON as dict
        """
        self._request_url_get(url)
        self._post_process_response()
        return self._return_response_text_object()

    def get_status(self, entry_subtype: str) -> str:
        """Get status from entry_subtype.

        This function is overriden in inheriting classes
        Returning 'Unknown' is kept from legacy scraper

        :param entry_subtype: used in subclasses
        :return: status string
        """
        return "Unknown"

    def make_backscrape_iterable(self, kwargs: dict) -> None:
        """Checks if backscrape start and end arguments have been passed
        by caller, and parses them accordingly

        :param kwargs: passed when initializing the scraper, may or
            may not contain backscrape controlling arguments
        :return None
        """
        start = kwargs.get("backscrape_start")
        end = kwargs.get("backscrape_end")

        if start:
            start = datetime.strptime(start, "%m/%d/%Y")
        else:
            start = self.first_opinion_date
        if end:
            end = datetime.strptime(end, "%m/%d/%Y")
        else:
            end = datetime.now()

        self.back_scrape_iterable = [(start, end)]

    def _download_backwards(self, dates: Tuple[date]) -> None:
        """Set date range from backscraping args and scrape

        :param dates: (start_date, end_date) tuple
        :return None
        """
        self.set_url(*dates)
        logger.info("Backscraping for range %s %s", *dates)
        self.html = self._download()
        self._process_html()
