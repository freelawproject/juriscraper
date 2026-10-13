from typing import TYPE_CHECKING

from httpx import Request, Response, Timeout
from lxml.html import HtmlElement
from typing_extensions import override

from juriscraper.lib.log_tools import make_default_logger
from juriscraper.pacer.reports import BaseReport

from .docket_report import BaseDocketReport

logger = make_default_logger()

if TYPE_CHECKING:
    from .http import PacerSession


class ListOfCreditors(BaseDocketReport[dict[str, str | None]], BaseReport):
    """Query and parse the List of Creditors report."""

    FORMAT_RAW_DATA_SERVICE = "https://ncrs.uscourts.gov/query/cmecf/index.adp"
    PATH = "cgi-bin/CredMatrixCase.pl"
    CACHE_ATTRS = ["metadata"]
    ERROR_STRINGS = BaseReport.ERROR_STRINGS + [
        "You entered a non-bankruptcy type case:",
    ]

    def __init__(
        self, court_id: str, pacer_session: "PacerSession | None" = None
    ) -> None:
        super().__init__(court_id)
        BaseReport.__init__(self, court_id, pacer_session)

        self._clear_caches()
        self._metadata: dict[str, str | None] | None = None
        if not court_id.endswith("b"):
            raise ValueError(
                "Unable to create object. Must use bankruptcy court abbreviation."
            )

    @override
    def _parse_text(self, text: str) -> None:
        self._clear_caches()
        super()._parse_text(text)

    @property
    @override
    def data(self) -> dict[str, str | None]:
        """Get all the data back from this endpoint."""
        if self.is_valid is False:
            return {}

        data = self.metadata.copy()
        return data

    @property
    def metadata(self) -> dict[str, str | None]:
        """Parse the raw data from the HTML file."""
        if self.is_valid is False:
            return {}

        if self._metadata is not None:
            return self._metadata

        try:
            if self.tree is None:
                raise ValueError(
                    "Parse a report before accessing its contents."
                )
            if not isinstance(self.tree, HtmlElement):
                raise TypeError("Expected an HTML tree for this report.")
            values: list[str] = self.tree.xpath(
                '//form[@name="bnc"]//input[@name="data"]/@value'
            )
            raw_data = values[0]
        except IndexError:
            raw_data = None
        meta_data: dict[str, str | None] = {
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

        if self.tree is None:
            raise ValueError("Parse a report before accessing its contents.")
        if not isinstance(self.tree, HtmlElement):
            raise TypeError("Expected an HTML tree for this report.")
        actions: list[str] = self.tree.xpath('//form[@method="POST"]/@action')
        action_value = actions[0]
        param = action_value.split("?")[1]
        return param

    async def download_file(self) -> Response | None:
        """Downloads the formated pipe-limited file using the
        FORMAT_RAW_DATA_SERVICE API.

        :return: The server's response if the file content is valid, or None if
        an error occurred.
        """

        if self.session is None:
            raise ValueError(
                "session attribute of ListOfCreditors cannot be None."
            )

        params = {
            "format": "rawdata",
            "useragentstring": "CM/ECF-BK V10.6.4",
            "data": self.metadata.get("data"),
        }
        req_timeout = Timeout(60, read=300)
        request = Request(
            "POST",
            self.FORMAT_RAW_DATA_SERVICE,
            params=params,
            extensions={"timeout": req_timeout.as_dict()},
        )
        r = await self.session.send(request)
        if "text/plain" in r.headers.get("content-type", ""):
            return r
        return None

    async def query_post_param(self) -> str:
        """To query the report and ensure that the cost is the same as in the
        browser, obtain a valid POST param 'x-L_1_0-1' from the input form.

        :return: A valid query POST param 'x-L_1_0-1'
        """
        if self.session is None:
            raise ValueError(
                "session attribute of ListOfCreditors cannot be None."
            )

        logger.info(f"Getting a valid POST param for '{self.court_id}'")
        self.response = await self.session.get(self.url)
        self.parse()
        return self._get_valid_post_param()

    async def query(
        self,
        pacer_case_id: str,
        docket_number: str,
        post_param: str,
    ) -> None:
        """Query the List of creditors report and return the results.

        :param pacer_case_id: The internal PACER ID for the case.
        :param docket_number: A docket number to look up. Something like
        2:17-bk-39239.

        :return: request response object
        """
        if self.session is None:
            raise ValueError(
                "session attribute of ListOfCreditors cannot be None."
            )

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
        self.response = await self.session.post(
            f"{self.url}?{post_param}", data=params
        )
        self.parse()
