"""Scraper for Wyoming Supreme Court
CourtID: wyo
Court Short Name: Wyo.
History:
 - 2014-07-02: mlr: Created new version when court got new website.
 - 2015-07-06: m4h7: Updated to use JSON!
 - 2016-06-09: arderyp: Updated because json endpoint moved and was changed
 - 2024-04-12: grossir: update to OpinionSiteLinear and implement dynamic backscraper
"""

import re
from datetime import date, datetime
from urllib.parse import urlencode

from pydantic import TypeAdapter
from typing_extensions import TypedDict, Unpack, override

from juriscraper.AbstractSite import SiteOptions, logger
from juriscraper.lib.string_utils import CaseNameTweaker
from juriscraper.lib.type_utils import BackscrapeOptions, ExtractedMetadata
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class _Opinion(TypedDict):
    DocumentName: str
    date_heard: str
    Appellant: str
    Appellee: str
    DocketNumber: str
    OpinionID: str


_opinions_adapter = TypeAdapter(list[_Opinion])


class Site(OpinionSiteLinear[tuple[date | None, date]]):
    json: list[_Opinion]

    date_re = re.compile(r"^/Date\((\d+)\)/$")
    base_url = "http://www.courts.state.wy.us"
    api_url = "https://opinions.courts.state.wy.us/Home/GetOpinions"
    document_url = (
        "https://stwjbopinions.blob.core.usgovcloudapi.net/wsc-opinions"
    )

    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions[tuple[date | None, date]]],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.court_id = self.__module__
        self.set_url(datetime(datetime.today().year, 1, 1))
        self.make_backscrape_iterable(kwargs)
        self.status = "Published"

    @override
    def _process_html(self) -> None:
        """Process HTML into case dictionaries

        :return: None
        """
        self.json = _opinions_adapter.validate_python(self.html, strict=True)

        for opinion in self.json:
            pdf_file_name = opinion["DocumentName"]
            if pdf_file_name[:5] == "../..":
                pdf_file_name = pdf_file_name[5:]
            url = f"{self.document_url}/{pdf_file_name}".replace(" ", "%20")

            match = self.date_re.match(opinion["date_heard"])
            if match is None:
                raise ValueError(
                    f"Invalid opinion date: {opinion['date_heard']!r}"
                )
            timestamp = int(match.group(1)) / 1000
            date_filed = datetime.fromtimestamp(timestamp).strftime("%m/%d/%Y")

            self.cases.append(
                {
                    "name": f"{opinion['Appellant']} v. {opinion['Appellee']}",
                    "url": url,
                    "date": date_filed,
                    "docket": opinion["DocketNumber"],
                    "citation": opinion["OpinionID"],
                }
            )

    def set_url(
        self, start: date | None = None, end: date | None = None
    ) -> None:
        """Sets self.url

        If neither StartDate or EndDate query string parameters
        are passed, the API returns all the dataset

        :param start: start date
        :param end: end date

        :return: None
        """
        params = {}

        if start is not None:
            params["StartDate"] = start.strftime("%m/%d/%Y")
        if end is not None:
            params["EndDate"] = end.strftime("%m/%d/%Y")

        if bool(params):
            self.url = f"{self.api_url}?{urlencode(params)}"
        else:
            self.url = self.api_url

    @override
    async def _download_backwards(
        self, dates: tuple[date | None, date]
    ) -> None:
        """Make custom date range request

        :param dates: (start_date, end_date) tuple
        :return None
        """
        logger.info("Backscraping for range %s %s", *dates)
        self.set_url(*dates)
        self.html = await self._download()
        self._process_html()

    @override
    def make_backscrape_iterable(self, kwargs: BackscrapeOptions) -> None:
        """Checks if backscrape start and end arguments have been passed
        by caller, and parses them accordingly

        :param kwargs: passed when initializing the scraper, may or
            may not contain backscrape controlling arguments
        :return None
        """
        start = kwargs.get("backscrape_start")
        end = kwargs.get("backscrape_end")

        if bool(start):
            start = datetime.strptime(start, "%m/%d/%Y")
        else:
            start = None
        if bool(end):
            end = datetime.strptime(end, "%m/%d/%Y")
        else:
            end = datetime.now()

        self.back_scrape_iterable = [(start, end)]

    @override
    def extract_from_text(self, scraped_text: str) -> ExtractedMetadata:
        """Extract lower court from the scraped text.

        :param scraped_text: The text to extract from.
        :return: A dictionary with the metadata.
        """
        metadata: ExtractedMetadata = {}
        lower_court_pattern = re.compile(
            r"Appeal\s+from\s+the\s+(?P<lower_court>.*?)[,\n]\s*The\s+Honorable\s+(?P<judge>.+?),\s*Judge",
            re.DOTALL,
        )
        lower_court = ""
        lower_court_judge = ""
        if (match := lower_court_pattern.search(scraped_text)) is not None:
            lower_court = re.sub(
                r"\s+", " ", match.group("lower_court")
            ).strip()
            lower_court_judge = match.group("judge").strip()

        if bool(lower_court):
            metadata.setdefault("Docket", {})["appeal_from_str"] = lower_court
        if bool(lower_court_judge):
            metadata.setdefault("OriginatingCourtInformation", {})[
                "assigned_to_str"
            ] = lower_court_judge

        return metadata
