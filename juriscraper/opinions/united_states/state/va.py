import re
from datetime import date, datetime, timedelta

from lxml.html import HtmlElement
from typing_extensions import Unpack, override

from juriscraper.AbstractSite import SiteOptions
from juriscraper.lib.string_utils import CaseNameTweaker, titlecase
from juriscraper.lib.type_utils import ExtractedMetadata
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    lower_court_regex = re.compile(r"FROM THE (?P<lower_court>.+)")

    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.court_id = self.__module__
        self.url = "http://www.courts.state.va.us/scndex.htm"
        self.status = "Published"
        self.should_have_results = True

    @override
    def _process_html(self) -> None:
        """Parses the HTML content to extract case information.

        :return: None
        """
        if self.test_mode_enabled():
            today = datetime.strptime("11/20/2023", "%m/%d/%Y").date()
        else:
            today = date.today()

        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        rows: list[HtmlElement] = self.html.xpath("//p")
        for row in rows:
            links = row.findall(".//a")
            if len(links) != 2:
                continue
            name: str = row.xpath(".//b/text()")[0].strip()

            text = row.text_content().split(name)[1].strip()
            split_test = text.split("\n")

            date_str = split_test[0].strip()
            summary = split_test[1].strip()

            if "Revised" in date_str:
                date_str = date_str.split("Revised")[1].strip().strip(")")
            date_object = datetime.strptime(date_str, "%m/%d/%Y").date()
            if date_object < today - timedelta(days=60):
                # Stop after two months
                break

            self.cases.append(
                {
                    "name": row.xpath(".//b/text()")[0].strip(),
                    "docket": links[1].text_content().strip(" '\""),
                    "url": links[1].attrib["href"],
                    "summary": summary,
                    "date": date_str,
                }
            )

    @override
    def extract_from_text(self, scraped_text: str) -> ExtractedMetadata:
        """Extract lower court from the scraped text.

        :param scraped_text: The text to extract from.
        :return: A dictionary with the metadata.
        """
        if (
            match := self.lower_court_regex.search(scraped_text[:1000])
        ) is not None:
            lower_court = re.sub(
                r"\s+", " ", match.group("lower_court")
            ).strip()
            return {
                "Docket": {
                    "appeal_from_str": titlecase(lower_court),
                }
            }

        return {}
