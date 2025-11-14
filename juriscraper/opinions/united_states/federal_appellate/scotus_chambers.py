from typing import Optional

from lxml.html import HtmlElement

from juriscraper.opinions.united_states.federal_appellate import (
    scotus_slip,
)


class Site(scotus_slip.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.status = "In-chambers"
        self.court = "in-chambers"
        self.url = f"{self.base_url}{self.court}.aspx"

    @staticmethod
    def get_fields(cells: list[HtmlElement], row: HtmlElement) -> Optional[tuple[HtmlElement]]:
        """
        Extract fields from a table row for in-chambers opinions.

        :params cells: list of HtmlElement objects representing the row's cells
                row: HtmlElement for the table row to extract fields from
        :return: tuple(date, docket, link, revised, justice, citation) or None
        """
        if len(cells) != 7:
            return None
        _, date, docket, link, revised, justice, citation = row.xpath(".//td")

        return date, docket, link, revised, justice, citation
