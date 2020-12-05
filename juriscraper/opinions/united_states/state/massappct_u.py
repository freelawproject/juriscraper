"""
Scraper for Massachusetts Appeals Court Rule 23.0 (formerly Rule 1:28)
CourtID: massappct
Court Short Name: Mass App Ct
Author: William Palin
Court Contact: SJCReporter@sjc.state.ma.us (617) 557-1030
Reviewer:
Date: 2020-02-27
"""

from datetime import date, timedelta
from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.string_utils import convert_date_string


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.homepage = "https://128archive.com"
        self.case_date = date.today()
        self.backwards_days = 14
        self.url = self.build_url()
        self.court_id = self.__module__
        self.court_identifier = "AC"

    def build_url(self):
        start_date = self.case_date - timedelta(days=self.backwards_days)
        url_template = 'https://128archive.com/?Action=search&DocketNumber=&PartyName=&ReleaseDateFrom=%s&ReleaseDateTo=%s&Keywords=&SortColumnName=Release+Date+Descending+Order&SortColumnName=Release+Date+Descending+Order&SortOrder=&CurrentPageNo=1&Pages=1&PageSize=100'
        return url_template % (start_date.strftime("%m/%d/%Y"), self.case_date.strftime("%m/%d/%Y"))

    def _download(self, request_dict={}):
        return super(Site, self)._download(request_dict)

    def _get_precedential_statuses(self):
        xp = './/div[contains(text(),"Case Name")]/following-sibling::div[1]'
        return ["Persuasive" for case_name in self.html.xpath(xp)]

    def _get_docket_numbers(self):
        xp = './/div[contains(text(),"Docket Number")]/following-sibling::div[1]'
        return [docket_number.text_content().strip() for docket_number in self.html.xpath(xp)]

