# Author: Michael Lissner
# Date created: 2013-05-23
from datetime import datetime

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.court_code = "S.Ct"
        self.status = "Published"

    def _process_html(self) -> None:
        """Parse HTML into case objects

        :return: None
        """
        for row in self.html.xpath("//tr[@class='row-']"):
            date, court, docket, name, lower_court, citation = row.xpath(
                ".//td")
            court = court.text_content()
            if court != self.court_code:
                continue

            if not docket.xpath(".//a"):
                continue

            name = name.text_content().split("(")[0]
            self.cases.append({
                "date": date.text_content(),
                "name": name,
                "docket": [docket.text_content().strip().split("\t")[0].split()[0]],
                "url": docket.xpath(".//a")[0].get("href"),
                "lower_court": lower_court.text_content(),
                "citation": [citation.text_content()],
            })

    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        self.url = f"https://www.courts.state.hi.us/opinions_and_orders/opinions/page/1?yr={start_date.year}&mo#038;mo"
        while True:
            self.parse()
            next = list(self.html.xpath("//div[@id='reg-pagination']//a"))
            self.downloader_executed=False
            if str(next[-1].text).__eq__('Next »'):
                self.url = next[-1].get('href')
            else:
                break
        return 0

    def get_state_name(self):
        return "Hawaii"

    def get_court_type(self):
        return "state"

    def get_court_name(self):
        return "Supreme Court of Hawaii"

    def get_class_name(self):
        return "haw"
