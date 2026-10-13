import re

from lxml.html import HtmlElement
from typing_extensions import Unpack, override

from juriscraper.AbstractSite import SiteOptions
from juriscraper.lib.string_utils import CaseNameTweaker
from juriscraper.lib.type_utils import ExtractedMetadata
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    court_code = "S"
    division = ""
    date_regex = re.compile(r" \d\d?/\d\d?/\d\d| filed")

    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions],
    ) -> None:
        kwargs.setdefault("verify", False)
        super().__init__(cnt, user_agent, **kwargs)
        self.court_id = self.__module__
        self.url = f"https://www.courts.ca.gov/cms/opinions.htm?Courts={self.court_code}"
        self.status = "Published"
        self.should_have_results = True

    @override
    def _process_html(self) -> None:
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        rows: list[HtmlElement] = self.html.xpath("//table/tr[not(th)]")
        for row in rows:
            name: str = row.xpath(".//*[@class='op-title']/text()")[0]

            split = self.date_regex.split(name)[0]
            if "P. v. " in split:
                case_name = split.replace("P. ", "People ")
            else:
                case_name = split

            url: str = row.xpath(".//a[@class='op-link']/@href")[0]
            date_filed: str = row.xpath(".//*[@class='op-date']/text()")[0]
            docket: str = row.xpath(".//*[@class='op-case']/text()")[0]
            case = {
                "name": case_name,
                "url": url,
                "date": date_filed,
                "docket": docket,
            }
            if bool(self.division):
                case["division"] = self.division

            self.cases.append(case)

    @override
    def extract_from_text(self, scraped_text: str) -> ExtractedMetadata:
        """Extract lower court and case number from the scraped text.

        :param scraped_text: The text to extract from.
        :return: A dictionary with the metadata.
        """
        pattern = re.compile(
            r"S\d+\s*\n"
            r"(?P<lower_court>.+?)\s*$"
            r"(\s*\n\s*)"
            r"(?P<lower_court_number>[A-Z0-9]{4,})\s*$",
            re.MULTILINE,
        )

        lower_court = ""
        lower_court_number = ""

        if (match := pattern.search(scraped_text)) is not None:
            lower_court = re.sub(
                r"\s+", " ", match.group("lower_court")
            ).strip()
            lower_court_number = match.group("lower_court_number").strip()

        result: ExtractedMetadata = {}
        if bool(lower_court) or bool(lower_court_number):
            if bool(lower_court):
                result["Docket"] = {}
                result["Docket"]["appeal_from_str"] = lower_court
            if bool(lower_court_number):
                result["OriginatingCourtInformation"] = {}
                result["OriginatingCourtInformation"]["docket_number"] = (
                    lower_court_number
                )

        return result
