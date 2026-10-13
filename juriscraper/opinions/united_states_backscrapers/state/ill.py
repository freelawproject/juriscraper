# History:
#   2015-10-20: Created by Andrei Chelaru

from datetime import datetime

from dateutil import parser
from lxml import html
from lxml.html import HtmlElement
from typing_extensions import Unpack, override

from juriscraper.AbstractSite import SiteOptions, logger
from juriscraper.lib.string_utils import CaseNameTweaker
from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite[int]):
    status: int
    year: int
    download_url_path: str
    case_name_path: str
    case_dates_path: str
    case_dates_path_day: str
    case_dates_path_month: str
    precedential_statuses_path: str
    docket_numbers_path: str

    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions[int]],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.court_id = self.__module__
        self.url = ""
        self.url_base = "http://www.illinoiscourts.gov/Opinions/SupremeCourt/{year}/default.asp"
        self.back_scrape_iterable = list(range(1996, 2015))
        self.neutral_citations_path: str | None = None
        self.__set_paths(1996)

    @override
    def _get_download_urls(self) -> list[str]:
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        texts: list[str] = self.html.xpath(self.download_url_path)
        return texts

    @override
    def _get_case_names(self) -> list[str]:
        case_names = []
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        elements: list[HtmlElement] = self.html.xpath(self.case_name_path)
        for e in elements:
            texts: list[str] = e.xpath(".//text()")
            case_names.append(" ".join(i.strip() for i in texts).strip())
        return case_names

    @override
    def _get_case_dates(self) -> list[datetime]:
        case_dates = []
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        elements: list[HtmlElement] = self.html.xpath(self.case_dates_path)
        if self.year <= 2006:
            for e in elements:
                month: str = "".join(
                    e.xpath(self.case_dates_path_month)
                ).strip()
                day: str = "".join(e.xpath(self.case_dates_path_day)).strip()
                month = month.replace("Decemberr", "December")
                try:
                    case_dates.append(
                        datetime.strptime(
                            f"{self.year} {month} {day}",
                            "%Y %B %d",
                        )
                    )
                except ValueError:
                    raise
        else:
            for d in elements:
                texts: list[str] = d.xpath(".//text()")
                case_dates.append(
                    parser.parse("".join(i.strip() for i in texts), fuzzy=True)
                )

        return case_dates

    @override
    def _get_precedential_statuses(self) -> list[str]:
        statuses = []
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        elements: list[HtmlElement] = self.html.xpath(
            self.precedential_statuses_path
        )
        for e in elements:
            s = html.tostring(e, method="text", encoding="unicode")
            if "NRel" in s:
                statuses.append("Unpublished")
            else:
                statuses.append("Published")
        return statuses

    @override
    def _get_docket_numbers(self) -> list[str]:
        docket_numbers = []
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        elements: list[HtmlElement] = self.html.xpath(self.docket_numbers_path)
        for e in elements:
            texts: list[str] = e.xpath(".//text()")
            nums = " ".join(i.strip() for i in texts)
            nums = nums.replace("Official Reports", "")
            docket_numbers.append(nums)
        return docket_numbers

    @override
    def _get_citations(self) -> list[str] | None:
        neutral_citations = None
        if bool(self.neutral_citations_path):
            neutral_citations = []
            if not isinstance(self.html, HtmlElement):
                raise ValueError(
                    "An HTML document must be downloaded before parsing."
                )
            elements: list[HtmlElement] = self.html.xpath(
                self.neutral_citations_path
            )
            for e in elements:
                texts: list[str] = e.xpath(".//text()")
                neutral_citations.append(
                    " ".join(i.strip() for i in texts).strip()
                )

        return neutral_citations

    @override
    async def _download_backwards(self, d: int) -> None:
        self.__set_paths(d)

        self.url = self.url_base.format(year=self.year)
        logger.info(f"Scraping year {self.year}")
        self.html = await self._download()
        if self.html is not None:
            # Setting status is important because it prevents the download
            # function from being run a second time by the parse method.
            self.status = 200

    def __set_paths(self, year: int) -> None:
        self.year = year
        if year < 2006:
            base_path = "//tr/td[4][a]"
            self.download_url_path = f"{base_path}/a[1]/@href"
            self.case_name_path = f"{base_path}/preceding-sibling::td[1]"
            self.case_dates_path = base_path
            self.case_dates_path_day = "./preceding-sibling::td[3]//text()"
            self.case_dates_path_month = ".//ancestor::tr[1]/preceding-sibling::tr[count(./td) = 1][td//strong][1]/td//text()"
            self.precedential_statuses_path = (
                f"{base_path}/preceding-sibling::td[2]"
            )
            self.docket_numbers_path = f"{base_path}/preceding-sibling::td[2]"
            self.neutral_citations_path = None
        elif 2006 <= year <= 2010:
            if year == 2010:
                base_path = "//tr/td[3][div/a]"
                self.download_url_path = f"{base_path}/div[1]/a[1]/@href"
                self.case_name_path = f"{base_path}/div[1]/a[1]"
            else:
                base_path = "//tr/td[3][a]"
                self.download_url_path = f"{base_path}/a[1]/@href"
                self.case_name_path = f"{base_path}/a[1]"
            if year == 2006:
                self.case_dates_path = base_path
                self.case_dates_path_day = "./preceding-sibling::td[2]//text()"
                self.case_dates_path_month = ".//ancestor::tr[1]/preceding-sibling::tr[count(./td) = 1][1]/td//text()"
            else:
                self.case_dates_path = f"{base_path}/preceding-sibling::td[2]"
            self.precedential_statuses_path = (
                f"{base_path}/preceding-sibling::td[1]"
            )
            self.docket_numbers_path = f"{base_path}/preceding-sibling::td[1]"
            self.neutral_citations_path = None
        elif 2010 < year < 2015:
            base_path = "//tr/td[4][div/a/text()]"
            self.download_url_path = f"{base_path}/div[1]/a[1]/@href"
            self.case_name_path = f"{base_path}/div[1]/a[1]"
            self.case_dates_path = f"{base_path}/preceding-sibling::td[3]"
            self.precedential_statuses_path = (
                f"{base_path}/preceding-sibling::td[2]"
            )
            self.docket_numbers_path = f"{base_path}/preceding-sibling::td[2]"
            self.neutral_citations_path = (
                f"{base_path}/preceding-sibling::td[1]"
            )
