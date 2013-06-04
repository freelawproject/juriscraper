"""Scraper for the Supreme Court of Michigan
CourtID: mich
Court Short Name: Mich."""

from juriscraper.GenericSite import GenericSite
from juriscraper.lib.string_utils import titlecase
import time
from datetime import date


class Site(GenericSite):
    def __init__(self):
        super(Site, self).__init__()
        self.url = ('http://courts.mi.gov/opinions_orders/opinions_orders/Pages/default.aspx?SearchType=4'
                   '&Status_Advanced=sct&FirstDate_Advanced=7%2f1%2f1996&LastDate_Advanced=3%2f1%2f2013')
        self.court_id = self.__module__

    def _get_case_dates(self):
        dates = []
        for txt in self.html.xpath('//li[@class="releaseDate"]/text()'):
            # Release Date: 2/22/2013 --> 2/22/2013
            txt = txt.strip().split(' ')[2]
            dates.append(date.fromtimestamp(time.mktime(time.strptime(
                txt.strip(), '%m/%d/%Y'))))
        return dates

    def _get_docket_numbers(self):
        docket_numbers = []
        for s in self.html.xpath('//li[@class="casenumber" and not(ancestor::ul[@class="result-header"])]'):
            docket_numbers.append(s.text)
        return docket_numbers

    def _get_case_names(self):
        case_names = []
        for case_name in self.html.xpath('//li[@class="title1" and not(ancestor::ul[@class="result-header"])]/a/text()'):
            case_name = titlecase(case_name)
            if 'People of Mi ' in case_name:
                case_name = case_name.replace('People of Mi ', 'People of Michigan ')
            case_names.append(case_name)
        return case_names

    def _get_download_urls(self):
        return [s for s in self.html.xpath('//li[@class="title1" and not(ancestor::ul[@class="result-header"])]/a/@href')]

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_names)

    def _get_lower_courts(self):
        lower_courts = []
        for s in self.html.xpath('//li[@class = "casedetailsleft"]//li[@class="lowerCourt"]/text()'):
            try:
                lower_courts.append(titlecase(s.strip().split(' ', 2)[2]))
            except IndexError:
                lower_courts.append('')
        return lower_courts

    def _get_dispositions(self):
        disps = []
        for s in self.html.xpath('//li[@class="caseNature"]/text()'):
            try:
                disps.append(s.strip().split(' ', 2)[2])
            except IndexError:
                # Happens when it's blank.
                disps.append('')
        return disps

    def _get_lower_court_numbers(self):
        nums = []
        for s in self.html.xpath('//li[@class = "casedetailsright"]//li[@class = "lowerCourt"]/text()'):
            try:
                nums.append(s.strip().split('No. ')[1])
            except IndexError:
                nums.append('')
        return nums

    def _download_backwards(self, page):
        if page <= 21711:
            self.url = "http://courts.mi.gov/opinions_orders/opinions_orders/Pages/default.aspx?SearchType=4&Status_Advanced=sct&FirstDate_Advanced=7%2f1%2f1996&LastDate_Advanced=3%2f1%2f2013&PageIndex=" + str(page)

        self.html = self._download()
