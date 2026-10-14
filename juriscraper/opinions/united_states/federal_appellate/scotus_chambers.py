"""
Court Contact: https://www.supremecourt.gov/contact/contact_webmaster.aspx
"""

from datetime import date

from lxml.html import HtmlElement
from typing_extensions import TypedDict, Unpack, override

from juriscraper.AbstractSite import RequestParameters, SiteOptions, logger
from juriscraper.lib.exceptions import InsanityException
from juriscraper.lib.string_utils import CaseNameTweaker, convert_date_string
from juriscraper.OpinionSite import OpinionSite


class _Revision(TypedDict):
    href: str
    date_string: str


class Site(OpinionSite[int]):
    required_headers = ["Date", "Docket", "Name", "J."]
    expected_headers = required_headers + ["Revised", "R-", "Pt."]
    justices = {
        "A": "Samuel Alito",
        "AB": "Amy Coney Barrett",
        "AS": "Antonin Scalia",
        "B": "Stephen Breyer",
        "BK": "Brett Kavanaugh",
        "D": "Decree",
        "DS": "David Souter",
        "EK": "Elana Kagan",
        "G": "Ruth Bader Ginsburg",
        "JS": "John Paul Stephens",
        "K": "Anthony Kennedy",
        "KJ": "Ketanji Brown Jackson",
        "NG": "Neil Gorsuch",
        "PC": "Per Curiam",
        "R": "John G. Roberts",
        "SS": "Sonia Sotomayor",
        "T": "Clarence Thomas",
    }

    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions[int]],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.court_id = self.__module__
        self.yy = self._get_current_term()
        self.back_scrape_iterable = list(range(5, int(self.yy) + 1))
        self.url_base = "https://www.supremecourt.gov/opinions"
        self.path_table = "//table[@class='table table-bordered']"
        self.path_row = f"{self.path_table}/tr[position() > 1]"
        self.precedential = "In-chambers"
        self.court = "in-chambers"
        self.url = None
        self.headers: list[str] = []
        self.cases: list[dict[str, str]] = []

    @staticmethod
    def _get_current_term() -> int | str:
        """The URLs for SCOTUS correspond to the term, not the calendar.

        The terms kick off on the first Monday of October, so we use October 1st
        as our cut off date.
        """
        today = date.today()
        term_cutoff = date(today.year, 10, 1)
        if today < term_cutoff:
            # Haven't hit the cutoff, return previous year.
            return int(today.strftime("%y")) - 1  # y3k bug!
        else:
            return today.strftime("%y")

    @override
    async def _download(
        self, request_dict: RequestParameters | None = None
    ) -> HtmlElement:
        if request_dict is None:
            request_dict = {}
        self.set_url()
        html = await super()._download(request_dict)
        if not isinstance(html, HtmlElement):
            raise TypeError("Expected an HTML opinion listing")
        self.extract_cases_from_html(html)
        return html

    def set_url(self) -> None:
        self.url = f"{self.url_base}/{self.court}.aspx"

    def set_table_headers(self, html: HtmlElement) -> None:
        # Do nothing if table is missing
        if bool(html.xpath(self.path_table)):
            path = f"{self.path_table}//th"
            cells: list[HtmlElement] = html.xpath(path)
            self.headers = [cell.text_content().strip() for cell in cells]
            # Ensure that expected/required headers are present
            if not set(self.required_headers).issubset(self.headers):
                raise InsanityException("Required table column missing")

    def extract_cases_from_html(self, html: HtmlElement) -> None:
        self.set_table_headers(html)
        rows: list[HtmlElement] = html.xpath(self.path_row)
        for row in rows:
            case, revisions = self.extract_case_data_from_row(row)
            if bool(case):
                # Below will raise key error is new judge key encountered (new SC judge appointed)
                case["judge"] = (
                    self.justices[case["J."]] if bool(case["J."]) else ""
                )
                self.cases.append(case)
                for revision_data in revisions:
                    revision = case.copy()
                    revision["Date"] = revision_data["date_string"]
                    revision["Name_Url"] = revision_data["href"]
                    self.cases.append(revision)

    def extract_case_data_from_row(
        self, row: HtmlElement
    ) -> tuple[dict[str, str], list[_Revision]]:
        case: dict[str, str] = {}
        revisions: list[_Revision] = []
        # Process each cell in row
        for cell_index, cell in enumerate(row.findall("./td")):
            text = cell.text_content().strip()
            # Skip rows with blank first cell
            if cell_index == 0 and not bool(text):
                break
            label = self.headers[cell_index]
            if label in ["R-", "Pt."]:
                # Ignore some columns that we don't need
                pass
            elif label == "Revised":
                # It is possible for an opinion to have
                # multiple revisions, so we need to iterate
                # over the links the the cell
                for anchor in cell.findall("a"):
                    revisions.append(
                        {
                            "href": anchor.xpath("@href")[0],
                            "date_string": anchor.text_content(),
                        }
                    )
            else:
                # Handle normal data cells
                case[label] = text
                href: list[str] = cell.xpath("./a/@href")
                if bool(href):
                    case[f"{label}_Url"] = href[0]
        return case, revisions

    @override
    def _get_case_names(self) -> list[str]:
        return [case["Name"] for case in self.cases]

    @override
    def _get_download_urls(self) -> list[str]:
        return [case["Name_Url"] for case in self.cases]

    @override
    def _get_case_dates(self) -> list[date | None]:
        return [convert_date_string(case["Date"]) for case in self.cases]

    @override
    def _get_docket_numbers(self) -> list[str]:
        return [case["Docket"] for case in self.cases]

    @override
    def _get_judges(self) -> list[str]:
        return [case["judge"] for case in self.cases]

    @override
    def _get_precedential_statuses(self) -> list[str]:
        return [self.precedential] * len(self.cases)

    @override
    async def _download_backwards(self, d: int) -> None:
        self.yy = str(d if d >= 10 else f"0{d}")
        logger.info(f"Running backscraper for year: 20{self.yy}")
        self.html = await self._download()
