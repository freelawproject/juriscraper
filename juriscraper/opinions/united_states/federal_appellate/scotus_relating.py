from lxml.html import HtmlElement

from juriscraper.opinions.united_states.federal_appellate import (
    scotus_slip,
)


class Site(scotus_slip.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.status = "Relating-to"
        self.court = "relatingtoorders"
        self.url = f"{self.base_url}{self.court}/{self.get_term()}"


    @staticmethod
    def get_fields(cells: list[HtmlElement], row: HtmlElement) -> tuple:
        """
        Extract fields from a table row for relating-to opinions.

        :params cells: list of HtmlElement objects representing the row's cells
                row: HtmlElement for the table row to extract fields from
        :return: tuple(date, docket, link, revised, justice, citation) or None
        """
        if len(cells) != 5:
            return None
        date, docket, link, justice, citation = row.xpath(".//td")
        return date, docket, link, None, justice, citation
