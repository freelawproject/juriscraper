from typing import Optional

import requests
from requests import Response

from juriscraper.pacer.reports import BaseReport

from ..lib.log_tools import make_default_logger
from .docket_report import BaseDocketReport

logger = make_default_logger()


class ListOfCreditors(BaseDocketReport, BaseReport):
    """Query and parse the List of Creditors report."""

    FORMAT_RAW_DATA_SERVICE = "https://ncrs.uscourts.gov/query/cmecf/index.adp"
    PATH = "cgi-bin/CredMatrixCase.pl"
    CACHE_ATTRS = ["metadata"]
    ERROR_STRINGS = BaseReport.ERROR_STRINGS + [
        "You entered a non-bankruptcy type case:",
    ]

    def __init__(self, court_id, pacer_session=None):
        BaseDocketReport.__init__(self, court_id)
        BaseReport.__init__(self, court_id, pacer_session)

        self._clear_caches()
        self._metadata = None
        assert court_id.endswith(
            "b"
        ), "Unable to create object. Must use bankruptcy court abbreviation."

    @property
    def data(self):
        """Get all the data back from this endpoint."""
        if self.is_valid is False:
            return {}

        data = self.metadata.copy()
        return data

    @property
    def metadata(self):
        """Parse the raw data from the HTML file."""
        if self.is_valid is False:
            return {}

        if self._metadata is not None:
            return self._metadata

        try:
            raw_data = self.tree.xpath(
                '//form[@name="bnc"]//input[@name="data"]/@value'
            )[0]
        except IndexError:
            raw_data = None
        meta_data = {
            "court_id": self.court_id,
            "data": raw_data,
        }
        self._metadata = meta_data
        return meta_data

    def _get_valid_post_param(self) -> str:
        """Get a valid POST param from the input form.
        From: /cgi-bin/CredMatrixCase.pl?209635477353597-L_1_0-1
            "209635477353597-L_1_0-1"
        return: A valid POST param to query the report.
        """

        action_value = self.tree.xpath('//form[@method="POST"]/@action')[0]
        param = action_value.split("?")[1]
        return param

    def download_file(self) -> Optional[Response]:
        """Downloads the formated pipe-limited file using the
        FORMAT_RAW_DATA_SERVICE API.

        :return: The server's response if the file content is valid, or None if
        an error occurred.
        """

        params = {
            "format": "rawdata",
            "useragentstring": "CM/ECF-BK V10.6.4",
            "data": self._metadata["data"],
        }
        req_timeout = (60, 300)
        r = requests.post(
            self.FORMAT_RAW_DATA_SERVICE, params=params, timeout=req_timeout
        )
        if "text/plain" in r.headers.get("content-type"):
            return r
        return None

    def query_post_param(self) -> str:
        """To query the report and ensure that the cost is the same as in the
        browser, obtain a valid POST param 'x-L_1_0-1' from the input form.

        :return: A valid query POST param 'x-L_1_0-1'
        """
        assert (
            self.session is not None
        ), "session attribute of ListOfCreditors cannot be None."

        logger.info(f"Getting a valid POST param for '{self.court_id}'")
        self.response = self.session.get(self.url)
        self.parse()
        return self._get_valid_post_param()

    def query(
        self,
        pacer_case_id: str,
        docket_number: str,
        post_param: str,
    ):
        """Query the List of creditors report and return the results.

        :param pacer_case_id: The internal PACER ID for the case.
        :param docket_number: A docket number to look up. Something like
        2:17-bk-39239.

        :return: request response object
        """
        assert (
            self.session is not None
        ), "session attribute of ListOfCreditors cannot be None."

        params = {
            "all_case_ids": pacer_case_id,
            "case_num": docket_number,
            "typfmt": "rawfrmt",  # Returns raw data.
            "SMG": "",  # Special mailing group empty.
        }

        logger.info(
            "Querying list of creditors for case ID '%s' in court '%s' "
            "with params %s",
            pacer_case_id,
            self.court_id,
            params,
        )
        self.response = self.session.post(
            f"{self.url}?{post_param}", data=params
        )
        self.parse()
