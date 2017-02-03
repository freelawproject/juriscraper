# Scraper for Louisiana Supreme Court
# CourtID: la
# Court Short Name: LA
# Author: Andrei Chelaru
# Reviewer: mlr
# Date: 2014-07-05

import re
import time
from lxml import html
from datetime import date

from juriscraper.lib.string_utils import titlecase
from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = 'http://www.lasc.org/news_releases/{year}/default.asp'.format(year=date.today().year)

    def _download(self, request_dict={}):
        html_l = OpinionSite._download(self)
        html_trees = []
        path = "//td[contains(./text(),'Opinion') or contains(./text(), 'PER CURIAM')]/preceding-sibling::td[1]//@href"
        for url in html_l.xpath(path)[:2]:
            html_tree = self._get_html_tree_by_url(url, request_dict)
            html_trees.append(html_tree)
        return html_trees

    def _get_case_names(self):
        case_names = []
        for html_tree in self.html:
            case_names.extend(self._add_case_names(html_tree))
        return case_names

    def _get_download_urls(self):
        download_urls = []
        for html_tree in self.html:
            download_urls.extend(self._add_download_urls(html_tree))
        return download_urls

    def _get_case_dates(self):
        case_dates = []
        for html_tree in self.html:
            case_dates.extend(self._add_dates(html_tree))
        return case_dates

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_dates)

    def _get_docket_numbers(self):
        docket_numbers = []
        for html_tree in self.html:
            docket_numbers.extend(self._add_docket_numbers(html_tree))
        return docket_numbers

    def _get_judges(self):
        judges = []
        for html_tree in self.html:
            judges.extend(self._add_judges(html_tree))
        return judges

    @staticmethod
    def _add_judges(html_tree):
        judges = []
        for e in html_tree.xpath("//strong[contains(., 'J.') or contains(., 'CURIAM')]"):
            text = html.tostring(e, method='text', encoding='unicode')
            text = ' '.join(text.split())
            match = re.search(r'(\w+\s*\w+,?\s?J?\.?)', text)
            if match:
                judge = match.group(1)
                judge = re.sub('^BY ', '', judge)
                if 'CURIAM' in judge:
                    preceding_judge = 'CURIAM'
                else:
                    preceding_judge = judge
                judges.extend([judge] * len(list(html_tree.xpath(
                    "//p[contains(., 'v.') or contains(., 'IN RE') or contains(., 'IN THE') or contains(., 'vs.')]"
                    "[preceding::strong[1][contains(., '{pre_jud}') or text()=':']]//a".format(
                        pre_jud=preceding_judge)))))
        nr_of_links = len(html_tree.xpath("//a[contains(., 'v.') or contains(., 'IN RE') or "
                                          "contains(., 'IN THE') or contains(., 'vs.')]"))
        nr_of_judges = len(judges)
        if nr_of_judges < nr_of_links:
            for i in range(nr_of_links - nr_of_judges):
                judges.insert(0, '')
        return judges

    @staticmethod
    def _add_dates(html_tree):
        dates = []
        text = ' '.join(list(html_tree.xpath("//text()[contains(normalize-space(), 'day of')]")))
        text = ' '.join(text.split())
        if text:
            match = re.search(r'\D*((\d{1,2})\w{2} day of (\w+),\s*(\d{4})).*', text)
            date_text = '{day}{month}{year}'.format(day=match.group(2), month=match.group(3), year=match.group(4))
            case_date = date.fromtimestamp(time.mktime(time.strptime(date_text, '%d%B%Y')))
            dates.extend([case_date] * len(html_tree.xpath("//p[contains(., 'v.') or "
                                                           "contains(., 'IN RE') or "
                                                           "contains(., 'IN THE') or "
                                                           "contains(., 'vs.')]//a")))
        return dates

    @staticmethod
    def _add_download_urls(html_tree):
        return list(html_tree.xpath("//p[contains(., 'v.') or contains(., 'IN RE') or "
                                    "contains(., 'IN THE') or contains(., 'vs.')]//a/@href"))

    @staticmethod
    def _add_case_names(html_tree):
        case_names = []
        for element in html_tree.xpath("//p[contains(., 'v.') or contains(., 'IN RE') or "
                                       "contains(., 'IN THE') or contains(., 'vs.')]//a"):
            text = ' '.join(list(element.xpath(".//text()")))
            text = ' '.join(text.split())
            if text:
                try:
                    case_name = re.search(r'(\d+ ?-\w{1,2} ?- ?\d+)(?!.*\d+ ?-\w{1,2} ?- ?\d+)\s*(.*)', text).group(2)
                    if case_name:
                        pass
                    else:
                        name_element = element.xpath("./parent::p[1]/text()")
                        text = ' '.join(name_element.split())
                        case_name = re.search(r'(\w+.+)+', text).group(1)
                except AttributeError:
                    case_name = re.search(r'(\w+.+)+', text).group(1)
                case_names.append(titlecase(case_name))

        return case_names

    @staticmethod
    def _add_docket_numbers(html_tree):
        docket_numbers = []
        for element in html_tree.xpath("//p[contains(., 'v.') or contains(., 'IN RE') or contains(., 'IN THE') or contains(., 'vs.')]//a"):
            text = ' '.join(list(element.xpath(".//text()")))
            text = ' '.join(text.split())
            if text:
                try:
                    docket_numbers.append(re.search(r'(\d+ ?-.*- ?\d+)\s*(.*)', text).group(1))
                except AttributeError:
                    name_element = element.xpath("./parent::p[1]//text()")
                    text2 = ' '.join(list(name_element))
                    text2 = ' '.join(text2.split())
                    if text2:
                        docket_numbers.append(re.search(r'(\d+ ?-.*- ?\d+)\s*(.*)', text2).group(1))
        return docket_numbers
