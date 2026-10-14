# Author: Michael Lissner
# Date created: 2013-06-03
# Date updated: 2020-02-25

import re

from pydantic import TypeAdapter
from typing_extensions import TypedDict, Unpack, override

from juriscraper.AbstractSite import SiteOptions, logger
from juriscraper.lib.exceptions import InvalidDocumentError
from juriscraper.lib.string_utils import CaseNameTweaker
from juriscraper.lib.type_utils import ExtractedMetadata
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class _Order(TypedDict):
    documentDescription: str
    caseNumber: str
    cTrackId: str
    fileDate: str
    title: str


_orders_adapter = TypeAdapter(list[_Order])


class Site(OpinionSiteLinear):
    # Home: https://juddocumentservice.mt.gov/getDailyOrders
    base_url = "https://juddocumentservice.mt.gov"
    download_base = f"{base_url}/getDocByCTrackId?DocId="
    cite_regex = r"((19|20)\d{2}\sMT\s\d{1,3}[A-Z]?)"

    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.court_id = self.__module__
        self.url = f"{self.base_url}/getDailyOrders"
        self.expected_content_types = []
        self.should_have_results = True

    @override
    def _process_html(self) -> None:
        for row in _orders_adapter.validate_python(self.html, strict=True):
            description = row["documentDescription"]
            if not description.startswith("Opinion"):
                # skip orders and just do opinions
                logger.info("Skipping row with description %s", description)
                continue

            status = (
                "Published" if "Published" in description else "Unpublished"
            )

            docket = row["caseNumber"]
            if docket.startswith("DA"):
                nature = "Direct Appeal"
            elif docket.startswith("OP"):
                nature = "Original Proceeding"
            elif docket.startswith("PR"):
                nature = "Professional Regulation"
            elif docket.startswith("AF"):
                nature = "Administrative File"
            else:
                nature = "Unknown"

            author = ""
            disposition = ""
            summary = ""
            if (
                author_match := re.search(
                    r"Justice (?P<author>.*?)\s*(?:author(ed)?|,|-|\.)",
                    description,
                    re.I,
                )
            ) is not None:
                author = author_match.group("author")
                disposition = description[author_match.end() :].strip(" .,-")
                disposition = disposition[:1].upper() + disposition[1:]
            else:
                summary = description

            self.cases.append(
                {
                    "url": self.download_base + row["cTrackId"],
                    "status": status,
                    "date": row["fileDate"],
                    "name": row["title"],
                    "docket": docket,
                    "nature_of_suit": nature,
                    "author": author,
                    "disposition": disposition,
                    "summary": summary,
                }
            )

    @override
    def extract_from_text(self, scraped_text: str) -> ExtractedMetadata:
        """Extract citation, and OriginatingCourtInformation from text

        :param scraped_text: Text of scraped content
        :return: date filed
        """
        result: ExtractedMetadata = {}
        first_text = scraped_text[:400]
        if (match := re.search(self.cite_regex, first_text)) is not None:
            result["Citation"] = match.group(0)

        lower_court_pattern = re.compile(
            r"""
                APPEAL\s+FROM:\s+
                (?P<lower_court>.*?)(?:,\s+Cause)
                (?:.*?No\.\s+(?P<lower_court_docket>[^\n,]+))?
                (?:.*?Honorable\s+(?P<judge>.+?),\s*Presiding\s*Judge)?
            """,
            re.X | re.DOTALL,
        )

        if (match := lower_court_pattern.search(scraped_text)) is not None:
            lower_court = re.sub(
                r"\s+", " ", match.group("lower_court")
            ).strip()
            result.setdefault("Docket", {})["appeal_from_str"] = lower_court
            lower_court_judge = match.group("judge")
            if bool(lower_court_judge):
                result.setdefault("OriginatingCourtInformation", {})[
                    "assigned_to_str"
                ] = lower_court_judge
            lower_court_docket = match.group("lower_court_docket")
            if bool(lower_court_docket):
                result.setdefault("OriginatingCourtInformation", {})[
                    "docket_number"
                ] = lower_court_docket

        docket_number_pattern = re.compile(r"(DA|OP)\s[0-9]{2}-[0-9]{4}")
        if (match := docket_number_pattern.search(scraped_text)) is not None:
            result.setdefault("Docket", {})["docket_number"] = match.group(0)

        return result

    @override
    @staticmethod
    def cleanup_content(content: str | bytes) -> str | bytes:
        """Raise an error if the content is invalid; otherwise just return it

        Not cleaning up in the common sense; but avoids ingesting error
        pages. This source does not mark the error page with an error status
        and does not have content type headers; so we can't detect the error
        through standard controls

        The content may be a string if it's a string error response, like in
        https://storage.courtlistener.com/txt/2025/01/17/mercer_v._dphhs.txt

        When the content is PDF bytes, it contains the
        'DOCUMENT UNAVAILABLE FOR VIEWING' string. However, we can't access
        that value directly on the bytes. Luckyly, all those PDFs have the
        same hash, so it won't be a big problem. Check #1323 for more info

        :param content: the downloaded content; maybe a string or PDF bytes
        :return: the downloaded content, unchanged
        """
        if isinstance(content, str) and (
            "No document found with CTrack ID" in content[:1000]
            or "Your support ID is" in content[:1000]
        ):
            raise InvalidDocumentError(content)

        return content
