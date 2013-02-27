"""Scraper for the United States Court of Appeals for Veterans Claims
CourtID: cavc
Court Short Name: Vet.App.
NOTE: If you modify this, make sure you know what you are doing and test it
as over 40 other backscrapers import this code and re-use parts of it."""

from juriscraper.GenericSite import GenericSite
import time
import datetime
from datetime import date

class Site(GenericSite):
    def __init__(self):
        super(Site, self).__init__()
        self.url = ('http://www.uscourts.cavc.gov/opinions.php')
        self.court_id = self.__module__

    def _get_case_dates(self):
        dates = []
        for txt in self.html.xpath('//ul[@id = "oasteps_boxes"]/li[1]//td[3]/text()'):
            dates.append(date.fromtimestamp(time.mktime(time.strptime(txt.strip(), '%d%b%y'))))
        return dates

    def _get_docket_numbers(self):
        return [txt for txt in self.html.xpath('//ul[@id = "oasteps_boxes"]/li[1]//td[2]//text()')]

    def _get_download_urls(self):
        return [txt for txt in self.html.xpath('//ul[@id = "oasteps_boxes"]/li[1]//td[2]/a/@href')]

    # http://en.wikipedia.org/wiki/United_States_Secretary_of_Veterans_Affairs
    # provided the names to append here for different opinion dates.
    # Covering all possibilities here makes the backscrapers simple.
    def _get_case_names(self):
        case_names = []
        dates = self._get_case_dates()
        plaintiffs = self.html.xpath('//ul[@id = "oasteps_boxes"]/li[1]//td[1]/text()')
        for txt, dat in zip(plaintiffs, dates):
            if dat > datetime.date(2009, 1, 20):
                case_names.append(txt + ' v. Shinseki')
            elif dat > datetime.date(2007, 12, 20):
                case_names.append(txt + ' v. Peake')
            elif dat > datetime.date(2007, 10, 1):
                case_names.append(txt + ' v. Mansfield')
            elif dat > datetime.date(2005, 1, 26):
                case_names.append(txt + ' v. Nicholson')
            elif dat > datetime.date(2001, 1, 23):
                case_names.append(txt + ' v. Principi')
            elif dat > datetime.date(2000, 7, 25):
                case_names.append(txt + ' v. Gober')
            elif dat > datetime.date(1998, 1, 2):
                case_names.append(txt + ' v. West')
            elif dat > datetime.date(1997, 7, 1):
                case_names.append(txt + ' v. Gober')
            elif dat > datetime.date(1993, 1, 22):
                case_names.append(txt + ' v. Brown')
            elif dat > datetime.date(1992, 9, 26):
                case_names.append(txt + ' v. Principi')
            else:
                case_names.append(txt + ' v. Derwinski')
        return case_names

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_names)
