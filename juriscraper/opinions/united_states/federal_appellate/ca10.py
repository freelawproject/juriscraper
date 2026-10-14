from lxml import html
from lxml.html import HtmlElement
from typing_extensions import Unpack, override

from juriscraper.AbstractSite import SiteOptions
from juriscraper.lib.string_utils import CaseNameTweaker, convert_date_string
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.url = (
            "http://www.ca10.uscourts.gov/opinions/new/daily_decisions.rss"
        )
        self.court_id = self.__module__

    @override
    def _process_html(self) -> None:
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        for item in self.html.findall(".//item"):
            description: str = item.xpath(".//description/text()")[-1]
            status = (
                "Published"
                if "Published Opinion" in description
                else "Unpublished"
            )
            docket = description.split()[1].strip()
            date_string: str = item.xpath(".//pubdate/text()")[0]
            date = convert_date_string(date_string)
            if date is None:
                raise ValueError("An opinion publication date is required")
            formatted_date = date.strftime("%Y-%m-%d")

            lower_court: str = (
                item.xpath(
                    ".//*[local-name()='dc:creator' or local-name()='creator']/text()"
                )[0]
                .split("-")[0]
                .strip()
            )

            self.cases.append(
                {
                    "url": html.tostring(
                        item.findall("link")[0], method="text"
                    )
                    .decode()
                    .replace("\\n", "")
                    .strip(),
                    "name": item.xpath(".//title/text()")[0],
                    "date": formatted_date,
                    "status": status,
                    "docket": docket,
                    "lower_court": lower_court,
                }
            )
