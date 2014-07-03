#Scraper for Minnesota Supreme Court
#CourtID: minn
#Court Short Name: MN
#Author: Andrei Chelaru
#Reviewer:
#Date: 2014-07-03


from juriscraper.OpinionSite import OpinionSite
import time
import re
from datetime import date


class Site(OpinionSite):
    def __init__(self):
        super(Site, self).__init__()
        self.court_id = self.__module__
        self.url = 'http://mn.gov/lawlib/archive/sct{short_year}q{quarter}.html'.format(
            short_year=date.today().strftime("%y"),
            quarter=(date.today().month - 1) // 3 + 1
        )

    def _get_case_names(self):
        path = ("//ul//li/text()[not(contains(., 'ORDERS ON PETITIONS FOR FURTHER REVIEW FILED')"
                " or contains(., 'NO OPINIONS FILED'))]")
        return list(self.html.xpath(path))

    def _get_download_urls(self):
        path = '''//ul//li//@href[contains(.,'ORA') or contains(.,'OPA')]'''
        return list(self.html.xpath(path))

    def _get_case_dates(self):
        path = '''//ul//h4/text()'''
        dates = self.html.xpath(path)
        last_date_index = len(dates) - 1
        case_dates = []
        for index, date_element in enumerate(dates):
            if index < last_date_index:
                path_2 = "//h4[{c}]/following-sibling::li/text()[count(.|//h4[{n}]/preceding-sibling::li/text())" \
                         "=count(//h4[{n}]/preceding-sibling::li/text()) and not(contains(., 'NO OPINIONS FILED') " \
                         "or contains(., 'ORDERS ON PETITIONS FOR FURTHER REVIEW FILED'))]".format(c=index + 1,
                                                                                                   n=index + 2)
            else:
                path_2 = "//h4[{c}]/following-sibling::li/text()[not(contains(., 'NO OPINIONS FILED') " \
                         "or contains(., 'ORDERS ON PETITIONS FOR FURTHER REVIEW FILED'))]".format(c=index + 1)
            d = date.fromtimestamp(time.mktime(time.strptime(re.sub(' ', '', str(date_element)), '%B%d,%Y')))
            case_dates.extend([d] * len(self.html.xpath(path_2)))
        return case_dates

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_names)

    def _get_docket_numbers(self):
        path = '''//ul//li/a/text()[not(contains(., 'List'))]'''
        return list(self.html.xpath(path))