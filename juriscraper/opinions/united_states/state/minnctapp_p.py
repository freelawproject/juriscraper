#Scraper for Minnesota Court of Appeals Published Opinions
#CourtID: minnctapp
#Court Short Name: MN
#Author: Andrei Chelaru
#Reviewer: mlr
#Date: 2014-07-03

from datetime import date
import time

from juriscraper.lib.date_utils import quarter
from juriscraper.opinions.united_states.state import minn
import re


class Site(minn.Site):
    # Only subclasses minn for the _download method.
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        d = date.today()
        self.url = "http://mn.gov/lawlib/archive/cap{short_year}q{quarter}.html".format(
            short_year=d.strftime("%y"),
            quarter=quarter(d.month)
        )

    def _get_case_names(self):
        path = "//li/text()[not(contains(., 'NO PUBLISHED OPINIONS FILED'))][normalize-space(.)]"
        return list(self.html.xpath(path))

    def _get_download_urls(self):
        path = "//li//@href[contains(., 'pdf')]"
        return list(self.html.xpath(path))

    def _get_case_dates(self):
        # remove <h4> child element of <li> elements and set them as their next
        # sibling. I looked for a hook for modifying self.html before the
        # attributes are parsed but I couldn't find one
        body_node = self.html.xpath("//body")[0]
        for li_node in body_node.xpath('.//li'):
            if li_node.xpath('./h4'):
                body_node.insert(body_node.index(li_node) + 1, li_node.xpath('./h4')[0])

        path = '''//body//h4/text()'''
        dates = self.html.xpath(path)
        last_date_index = len(dates) - 1
        case_dates = []
        for index, date_element in enumerate(dates):
            if index < last_date_index:
                path_2 = "//h4[{c}]/following-sibling::li/text()[count(.|//h4[{n}]/preceding-sibling::li/text())" \
                         "=count(//h4[{n}]/preceding-sibling::li/text()) and " \
                         "not(contains(., 'NO PUBLISHED OPINIONS FILED'))][normalize-space(.)]".format(c=index + 1,
                                                                                   n=index + 2)
            else:
                path_2 = "//h4[{c}]/following-sibling::li/text()" \
                         "[not(contains(., 'NO PUBLISHED OPINIONS FILED'))][normalize-space(.)]".format(c=index + 1)
            d = date.fromtimestamp(time.mktime(time.strptime(re.sub(' ', '', str(date_element)), '%B%d,%Y')))
            case_dates.extend([d] * len(self.html.xpath(path_2)))
        return case_dates

    def _get_docket_numbers(self):
        path = '''//li/a/text()'''
        return list(self.html.xpath(path))
