import time
from datetime import date

from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.string_utils import titlecase
from juriscraper.AbstractSite import logger


class Site(OpinionSite):
    def __init__(self):
        super(Site, self).__init__()
        self.url = 'http://www.supremecourt.gov/opinions/slipopinions.aspx'
        self.court_id = self.__module__
        self.back_scrape_url = 'http://www.supremecourt.gov/opinions/slipopinion/{}'
        self.back_scrape_iterable = range(6, 16)

    def _get_case_names(self):
        return [titlecase(text) for text in
                self.html.xpath('//div[@id = "mainbody"]//table//tr/td/a/text()')]

    def _get_download_urls(self):
        path = '//div[@id = "mainbody"]//table//tr/td/a[text()]/@href'
        return [e for e in self.html.xpath(path)]

    def _get_case_dates(self):
        path = '//div[@id = "mainbody"]//table//tr/td[2]/text()'
        case_dates = []
        for date_string in self.html.xpath(path):
            try:
                case_date = date.fromtimestamp(time.mktime(time.strptime(date_string, '%m/%d/%y')))
            except ValueError:
                case_date = date.fromtimestamp(time.mktime(time.strptime(date_string, '%m-%d-%y')))
            case_dates.append(case_date)
        return case_dates

    def _get_docket_numbers(self):
        path = '//div[@id = "mainbody"]//table//tr/td[3]/text()'
        return [docket_number for docket_number in self.html.xpath(path)]

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_names)

    def _get_summaries(self):
        path = '//div[@id = "mainbody"]//table//tr//td/a/text()'
        return [summary for summary in self.html.xpath(path)]

    def _download_backwards(self, d):
        logger.info("Running backscraper for year: 20{}".format(d))
        self.url = self.back_scrape_url.format(d if d >= 10 else '0{}'.format(d))
        self.html = self._download()
        if self.html is not None:
            # Setting status is important because it prevents the download
            # function from being run a second time by the parse method.
            self.status = 200
