### BROKEN: Timeout #### Scraper and Back Scraper for New York Appellate Term 1st Dept.
# CourtID: nyappterm_1st
# Court Short Name: NY
# Author: Andrei Chelaru
# Reviewer: mlr
# Date: 2015-10-30

from datetime import date, timedelta
from lxml import html
from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.string_utils import convert_date_string


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court = "Appellate+Term,+1st+Dept"
        self.url = "http://iapps.courts.state.ny.us/lawReporting/Search"
        self.data = {
            "rbOpinionMotion": "opinion",
            "dtStartDate": (date.today() - timedelta(days=30)).strftime(
                "%m/%d/%Y"
            ),
            "dtEndDate": date.today().strftime("%m/%d/%Y"),
            "court": self.court,
            "Order_By": "Decision Date",
            "Submit": "Find",
        }
        self.court_id = self.__module__

    def _download(self, request_dict={}):
        response = self.request["session"].post(self.url, data=self.data)
        return html.fromstring(response.text).xpath(
            '//a[contains(@href, "reporter")]/./../../..'
        )

    def _get_case_names(self):
        return [
            x.xpath("./td[1]")[0].text_content().strip() for x in self.html
        ]

    def _get_download_urls(self):
        return [x.xpath(".//a/@href")[0] for x in self.html]

    def _get_case_dates(self):
        return [
            convert_date_string(x.xpath("./td[2]//text()")[0].strip())
            for x in self.html
        ]

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_names)

    def _get_docket_numbers(self):
        return [x.xpath("./td[5]//text()")[0].strip() for x in self.html]

    def _get_judges(self):
        return [
            x.xpath("./td[6]")[0].text_content().strip() for x in self.html
        ]

    def _get_neutral_citations(self):
        return [x.xpath(".//a")[0].text_content().strip() for x in self.html]
