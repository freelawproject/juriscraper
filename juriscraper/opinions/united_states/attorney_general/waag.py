"""
Scraper for Washington Attorney General
CourtID: waag
Court Short Name: Wash AG
Author: William E. Palin
History:
 - 2023-01-29: Created.
"""
from datetime import datetime as dt

from lxml import html

from juriscraper.lib.html_utils import get_html_parsed_text
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.status = "Published"
        self.year = dt.today().year
        self.url = f"https://www.atg.wa.gov/ago-opinions/year/{self.year}"

    def _process_html(self):
        """Process html

        :return: None
        """
        for row in self.html.xpath(
            ".//div/div[contains(@class, 'view-content')]/div"
        ):
            docket, date = row.xpath(".//div")[0].text_content().split(">")
            name = row.xpath(".//div")[2].text_content().strip()
            summary = row.xpath(".//div")[3].text_content().strip()
            url = row.xpath(".//div/span/a/@href")[0]
            self.cases.append(
                {
                    "url": url,
                    "docket": docket.strip(),
                    "name": name,
                    "date": date.strip(),
                    "summary": summary,
                }
            )

    @staticmethod
    def cleanup_content(content) -> str:
        """Process the HTML into content because PDF doesnt exist

        :param content: Page content to cleanup
        :return: Cleaned up HTML content
        """
        tree = get_html_parsed_text(content)
        core_element = tree.xpath(".//section[@id='content']")[0]
        return (core_element.text or "") + "".join(
            [
                html.tostring(child, pretty_print=True, encoding="unicode")
                for child in core_element.iterchildren()
            ]
        )
