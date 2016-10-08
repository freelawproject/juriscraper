"""Scraper for Supreme Court of U.S. OYEZ
CourtID: scotusoyez
Court Short Name: scotusoyez
Author: Andrei Chelaru
Reviewer:
Date created: 20 July 2014
"""

from datetime import datetime, date

from juriscraper.OralArgumentSite import OralArgumentSite


class Site(OralArgumentSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        d = date.today()
        # page_nr can be between 0 and 5
        page_nr = 0
        self.url = 'http://www.oyez.org/cases/{year}?page={nr}'.format(
            year=d.year - 1,
            nr=page_nr
        )
        self.extender = {}

    def _get_download_urls(self):
        path = "//td[contains(concat(' ',@class,' '),' views-field-field-argument-value')][contains(., '/')]/preceding-sibling::td[2]/a/@href"
        download_urls = []
        for index, e in enumerate(self.html.xpath(path)):
            case_html = self._get_html_tree_by_url(e)
            path = "//a[contains(concat(' ',@class,' '),' arg-link audio') and contains(., 'Download')]/@href"
            urls = list(case_html.xpath(path))
            if len(urls) == 0:
                download_urls.append('')
                self.extender[index] = 1
            else:
                download_urls.extend(urls)
                self.extender[index] = len(urls)
        return download_urls

    def _get_case_names(self):
        path = "//td[contains(concat(' ',@class,' '),' views-field-field-argument-value')][contains(., '/')]/preceding-sibling::td[2]/a/text()"
        return list(self.html.xpath(path))

    def _get_case_dates(self):
        path = "//td[contains(concat(' ',@class,' '),' views-field-field-argument-value')][contains(., '/')]/span/text()"
        return map(self._return_case_date, self.html.xpath(path))

    @staticmethod
    def _return_case_date(e):
        e = ''.join(e.split())
        return datetime.strptime(e, '%m/%d/%Y').date()

    def _get_docket_numbers(self):
        path = "//td[contains(concat(' ',@class,' '),' views-field-field-argument-value')][contains(., '/')]/preceding-sibling::td[1]/text()"
        return map(self._return_docket_number, self.html.xpath(path))

    @staticmethod
    def _return_docket_number(e):
        e = ''.join(e.split())
        return e

    def _post_parse(self):
        self.docket_numbers = self._extend_result(self.docket_numbers)
        self.case_dates = self._extend_result(self.case_dates)
        self.case_names = self._extend_result(self.case_names)

    def _extend_result(self, result):
        new_result = []
        for index, nr in enumerate(self.extender.values()):
            new_result.extend([result[index]] * nr)
        return new_result
