"""Scraper for the Supreme Court of Michigan
CourtID: mich
Court Short Name: Mich.
Contact: sitefeedback@courts.mi.gov
History:
 - 2014-09-21: Updated by Jon Andersen to handle some fields being missing
 - 2014-08-05: Updated to have a dynamic URL, an oversight during check in.
"""

from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.string_utils import titlecase, clean_if_py3
import time
from datetime import date, timedelta


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.today = date.today()
        self.a_while_ago = date.today() - timedelta(days=30)
        self.url = ('http://courts.mi.gov/opinions_orders/opinions_orders/'
                    'Pages/default.aspx?SearchType=4'
                    '&Status_Advanced=sct&FirstDate_Advanced='
                    '{start_month}%2f{start_day}%2f{start_year}'
                    '&LastDate_Advanced='
                    '{end_month}%2f{end_day}%2f{end_year}'.format(
            start_day=self.a_while_ago.day,
            start_month=self.a_while_ago.month,
            start_year=self.a_while_ago.year,
            end_day=self.today.day,
            end_month=self.today.month,
            end_year=self.today.year,
        ))
        self.back_scrape_iterable = range(0, 868)
        self.court_id = self.__module__

    def _get_case_dates(self):
        dates = []
        for txt in self.html.xpath('//li[@class="releaseDate"]/text()'):
            # Release Date: 2/22/2013 --> 2/22/2013
            txt = clean_if_py3(txt).strip().split(' ')[2]
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
        for el in self.html.xpath("//ul[contains(@class, 'odd') or contains(@class, 'even')]"):
            try:
                s = el.xpath('//li[@class="casedetailsleft"]'
                             '//li[@class="lowerCourt"]/text()')
                lower_courts.append(titlecase(clean_if_py3(s[0]).strip().split(' ', 2)[2]))
            except IndexError:
                lower_courts.append('')
        return lower_courts

    def _get_dispositions(self):
        disps = []
        for el in self.html.xpath("//ul[contains(@class, 'odd') or contains(@class, 'even')]"):
            try:
                s = el.xpath('//li[@class="caseNature"]/text()')
                disps.append(clean_if_py3(s[0]).strip().split(' ', 2)[2])
            except IndexError:
                disps.append('')
        return disps

    def _get_lower_court_numbers(self):
        nums = []
        for el in self.html.xpath("//ul[contains(@class, 'odd') or contains(@class, 'even')]"):
            try:
                s = el.xpath('//li[@class = "casedetailsright"]'
                             '//li[@class = "lowerCourt"]/text()')
                nums.append(clean_if_py3(s[0]).strip().split('No. ')[1])
            except IndexError:
                nums.append('')
        return nums

    def _download_backwards(self, page):
        self.url = "http://courts.mi.gov/opinions_orders/opinions_orders/Pages/default.aspx?SearchType=4&Status_Advanced=sct&FirstDate_Advanced=3%2f1%2f2013&LastDate_Advanced=8%2f8%2f2014&PageIndex=" + str(page)
        time.sleep(6)  # This site throttles if faster than 2 hits / 5s.
        self.html = self._download()
