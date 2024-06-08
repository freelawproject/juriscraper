from datetime import date, datetime
from typing import Tuple
from urllib.parse import urlencode

from juriscraper.AbstractSite import logger
from juriscraper.lib.date_utils import make_date_range_tuples
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    # This URL will show most recent opinions
    base_url = "https://www.ca1.uscourts.gov/opn/aci"
    days_interval = 5
    first_opinion_date = datetime(2003, 3, 23)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = self.base_url
        self.make_backscrape_iterable(kwargs)

    def _process_html(self):
        for row in self.html.xpath("//tr[not(th)]"):
            title = row.xpath("td[2]/a/text()")[0]
            url = row.xpath("td[2]/a/@href")[0]
            status = self.get_status_from_opinion_title(title)
            docket = row.xpath("td[3]/a/text()")[0]
            date_filed = row.xpath("td[1]/span/text()")[0]
            name = row.xpath("td[4]/text()")[0]
            lower_court = row.xpath("td[4]/span/text()")[0]
            self.cases.append(
                {
                    "name": name.strip(),
                    "url": url,
                    "date": date_filed,
                    "status": status,
                    "docket": docket,
                    "lower_court": lower_court,
                }
            )

    def get_status_from_opinion_title(self, title: str) -> str:
        """Status is encoded in opinion's link title

        :param title: opinion title. Ex: 23-1667P.01A, 23-1639U.01A

        :return: status string
        """
        if "U" in title:
            status = "Unpublished"
        elif "P" in title:
            status = "Published"
        elif "E" in title:
            status = "Errata"
        else:
            status = "Unknown"
        return status

    def _download_backwards(self, dates: Tuple[date]) -> None:
        """Change URL to backscraping date range

        :param dates: tuple with date range to scrape
        :return None
        """
        start, end = dates
        params = {
            "field_opn_csno_value_op": "starts",
            "field_opn_issdate_value[min][date]": start.strftime("%m/%d/%Y"),
            "field_opn_issdate_value[max][date]": end.strftime("%m/%d/%Y"),
        }
        self.url = f"{self.base_url}?{urlencode(params)}"
        self.html = self._download()
        self._process_html()

    def make_backscrape_iterable(self, kwargs: dict) -> None:
        """Checks if backscrape start and end arguments have been passed
        by caller, and parses them accordingly

        :param kwargs: passed when initializing the scraper, may or
            may not contain backscrape controlling arguments
        :return None
        """
        start = kwargs.get("backscrape_start")
        end = kwargs.get("backscrape_end")

        if start:
            start = datetime.strptime(start, "%m/%d/%Y")
        else:
            start = self.first_opinion_date
        if end:
            end = datetime.strptime(end, "%m/%d/%Y")
        else:
            end = datetime.now()

        self.back_scrape_iterable = make_date_range_tuples(
            start, end, self.days_interval
        )
