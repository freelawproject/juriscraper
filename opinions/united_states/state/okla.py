# Scraper for Supreme Court of Oklahoma
#CourtID: okla
#Court Short Name: OK
#Author: Andrei Chelaru
#Reviewer:
#Date: 2014-07-05

from datetime import date
import time
import re

from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(self):
        super(Site, self).__init__()
        self.court_id = self.__module__
        d = date.today()
        self.general_path = "//a[contains(./text(), '{year}')]".format(year=d.year)
        self.url = 'http://www.oscn.net/applications/oscn/Index.asp?ftdb=STOKCSSC&year={year}&level=1'.format(
            year=d.year
        )

    def _get_download_urls(self):
        path = "{gen_path}/@href".format(gen_path=self.general_path)
        return list(self.html.xpath(path))

    def _get_case_names(self):
        path = "{gen_path}/text()".format(gen_path=self.general_path)
        case_names = []
        for text in self.html.xpath(path):
            case_name = re.search('([^,]+), (\d{2}.\d{2}.\d{4}), (.*)', text).group(3)
            case_names.append(case_name)
        return case_names

    def _get_case_dates(self):
        path = "{gen_path}/text()".format(gen_path=self.general_path)
        case_dates = []
        for text in self.html.xpath(path):
            case_date = re.search('([^,]+), (\d{2}.\d{2}.\d{4}), (.*)', text).group(2)
            d = date.fromtimestamp(time.mktime(time.strptime(case_date, '%m/%d/%Y')))
            case_dates.append(d)
        return case_dates

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_names)

    def _get_neutral_citations(self):
        path = "{gen_path}/text()".format(gen_path=self.general_path)
        neutral_citations = []
        for text in self.html.xpath(path):
            neutral_citation = re.search('([^,]+), (\d{2}.\d{2}.\d{4}), (.*)', text).group(1)
            neutral_citations.append(neutral_citation)
        return neutral_citations