# Author: Michael Lissner
# History:
# - 2013-06-11: Birth.
# - 2013-08-06: Revised by Brian Carver
# - 2014-08-05: Updated URL by mlr
# - 2021-12-28: Updated by flooie
# - 2024-04-11: grossir, Merge backscraper and scraper; implement dynamic backscraper

import re
from datetime import datetime
from typing import Any, Dict

from juriscraper.AbstractSite import logger
from juriscraper.lib.html_utils import get_row_column_text
from juriscraper.lib.string_utils import titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    start_year = 1996

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.status = "Published"
        self.url = "https://ujs.sd.gov/Supreme_Court/opinions.aspx"
        self.is_backscrape = False
        self.make_backscrape_iterable(kwargs)

    def _process_html(self) -> None:
        """Parse HTML into case dictionaries

        :return None
        """
        rows = self.html.xpath(
            "//div[@id='ContentPlaceHolder1_ChildContent1_UpdatePanel_Opinions']//tbody/tr"
        )
        for row in rows:
            title = get_row_column_text(row, 2)
            cite = re.findall(r"\d{4} S\.D\. \d+", title)
            if not cite:
                continue

            # https://ujs.sd.gov/uploads/sc/opinions/2928369ef9a6.pdf
            # We abstract out the first part of the docket number here
            # And process the full docket number in the `extract_from_text` method
            # Called after the file has been downloaded.
            url = row.xpath(".//td[2]/a/@href")[0]
            docket = url.split("/")[-1][:5]
            self.cases.append(
                {
                    "date": get_row_column_text(row, 1),
                    "name": titlecase(title.rsplit(",", 1)[0]),
                    "citation": cite[0],
                    "url": url,
                    "docket": docket,
                }
            )

        if self.is_backscrape:
            page_count = self.html.xpath(
                "//span[@id='ContentPlaceHolder1_ChildContent1_Label_Page']"
            )[0].text_content()
            page_of = re.findall(r"Page (\d+) of (\d+)", page_count)

            if len(set(page_of[0])) == 1:
                return

            logger.info(
                "Getting page %s of %s", int(page_of[0][0]) + 1, page_of[0][1]
            )
            self.get_next_page()
            self._process_html()

    def get_next_page(self) -> None:
        """Gets next page"""
        view_state = self.html.xpath("//input[@id='__VIEWSTATE']/@value")[0]
        event_validation = self.html.xpath(
            "//input[@id='__EVENTVALIDATION']/@value"
        )[0]
        data = {
            "ctl00$ctl00$ScriptManager1": "ctl00$ctl00$ContentPlaceHolder1$ChildContent1$UpdatePanel_Opinions|ctl00$ctl00$ContentPlaceHolder1$ChildContent1$LinkButton_Next",
            "__EVENTTARGET": "ctl00$ctl00$ContentPlaceHolder1$ChildContent1$LinkButton_Next",
            "__VIEWSTATE": view_state,
            "__EVENTVALIDATION": event_validation,
        }
        self.parameters = data
        self.html = super()._download()

    def _download_backwards(self, year: int) -> None:
        """Get input year's page

        We need to GET the homepage first to load hidden inputs
        Then, we can POST for the desired year's page

        :param year:
        :return: None
        """
        logger.info("Backscraping for year %s", year)
        self.is_backscrape = True

        self.method = "GET"
        self.html = super()._download()
        view_state = self.html.xpath("//input[@id='__VIEWSTATE']/@value")[0]
        event_validation = self.html.xpath(
            "//input[@id='__EVENTVALIDATION']/@value"
        )[0]
        a = self.html.xpath(
            f".//a[contains(@id,'ContentPlaceHolder1_ChildContent1_Repeater_OpinionsYear_LinkButton1')][contains(text(), '{year}')]/@href"
        )
        link = a[0].split("'")[1]
        data = {
            "__VIEWSTATE": view_state,
            "__EVENTVALIDATION": event_validation,
            "__EVENTTARGET": link,
        }
        self.parameters = data
        self.method = "POST"
        self.html = super()._download()
        self._process_html()

    def make_backscrape_iterable(self, kwargs: Dict) -> None:
        """Creates backscrape iterable from kwargs or defaults

        :param kwargs: passed when initializing the scraper, may or
            may not contain backscrape controlling arguments
        :return None
        """
        start = kwargs.get("backscrape_start")
        end = kwargs.get("backscrape_end")

        start = int(start) if start else self.start_year
        end = int(end) + 1 if end else datetime.today().year

        self.back_scrape_iterable = range(start, end)

    def extract_from_text(self, scraped_text: str) -> Dict[str, Any]:
        """Can we extract the date filed from the text?

        :param scraped_text: The content of the document downloaded
        :return: Metadata to be added to the case
        """

        # The docket number appears to be the first text on the page.
        # So we crop the text to avoid any confusion that might occur in the
        # body of an opinion.
        docket = re.findall(r"#\d+.*-.-\w{3}", scraped_text[:100])
        if not docket:
            return {}

        metadata = {
            "Docket": {
                "docket_number": docket[0],
            },
        }
        return metadata
