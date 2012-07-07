"""Scraper for the United States Court of Federal Claims
CourtID: uscfc
Court Short Name: Fed. Cl."""

from juriscraper.GenericSite import GenericSite
from juriscraper.lib.string_utils import titlecase
import time
from datetime import date
import re
from lxml import html


class Site(GenericSite):
    def __init__(self):
        super(Site, self).__init__()
        self.url = 'http://www.uscfc.uscourts.gov/opinions_decisions_general/Published'
        self.court_id = self.__module__

    def _get_case_dates(self):
        dates = []
        for txt in self.html.xpath('//div[2]/table/tbody/tr/td/span/text()'):
            dates.append(date.fromtimestamp(time.mktime(time.strptime(
                txt.strip(), '%m/%d/%Y'))))
        return dates

    def _get_judges(self):
        judges = []
        for txt in self.html.xpath('//div[2]/table/tbody/tr/td[2]/text()'):
            judges.append(txt)
        return judges

    def _get_case_names(self):
        case_names = []
        for txt in self.html.xpath('//div[2]/table/tbody/tr/td[3]/text()'):
            case_names.append(titlecase(txt.strip()[:-8].replace('[', '')))
        return case_names

    def _get_docket_numbers(self):
        regex = re.compile("\d\d.\d*[a-zA-Z]")
        return [regex.search(html.tostring(ele, method='text', encoding='unicode')).group(0)
                    for ele in self.html.xpath('//div[2]/table/tbody/tr/td[3]')]

    def _get_summaries(self):
        summaries = []
        for txt in self.html.xpath('//div[2]/table/tbody/tr/td[4]/a/text()'):
            summaries.append(txt)
        return summaries

    def _get_download_urls(self):
        download_urls = []
        for url in self.html.xpath('//div[2]/table/tbody/tr/td[4]/a/@href'):
            download_urls.append(url)
        return download_urls

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_names)
