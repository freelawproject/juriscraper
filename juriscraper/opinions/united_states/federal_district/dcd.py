"""Scraper for United States District Court for the District of Columbia
CourtID: dcd
Court Short Name: D.D.C.
Author: V. David Zvenyach
Date created: 2014-02-27
Substantially Revised: Brian W. Carver, 2014-03-28
"""

import time
from datetime import date
from lxml import html
import re

from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.string_utils import titlecase


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = 'https://ecf.dcd.uscourts.gov/cgi-bin/Opinions.pl?' + str(date.today().year)

    def _get_download_urls(self):
        # There are often multiple documents and hence urls for each case.
        # This requires us to pad every other metadata field to match the
        # number of urls we find here.
        path = '//table[2]//tr[position()>0]/td[3]/a/@href'
        return [url for url in self.html.xpath(path)]

    def _get_case_names(self):
        casenames = []
        rowpath = '//table[2]//tr[position()>0]'
        cnpath = './td[2]//text()[preceding-sibling::br]'
        urlpath = './td[3]/a/@href'
        for row in self.html.xpath(rowpath):
            case_list = row.xpath(cnpath)
            for rough_case_name in case_list:
                case_name = titlecase(rough_case_name.lower())
                # Determine the number of urls in each row and pad the case
                # name list sufficiently
                count = len(row.xpath(urlpath))
                casenames.extend([case_name] * count)
        return casenames

    def _get_case_dates(self):
        dates = []
        rowpath = '//table[2]//tr[position()>0]'
        datepath = './td[1]/text()'
        urlpath = './td[3]/a/@href'
        for row in self.html.xpath(rowpath):
            date_string = row.xpath(datepath)
            for d in date_string:
                date_object = date.fromtimestamp(
                      time.mktime(time.strptime(d, '%m/%d/%Y')))
                # Determine the number of urls in each row and pad the date
                # list sufficiently
                count = len(row.xpath(urlpath))
                dates.extend([date_object] * count)
        return dates

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_names)

    def _get_docket_numbers(self):
        docket_numbers = []
        rowpath = '//table[2]//tr[position()>0]'
        dktpath = './td[2]//text()[following-sibling::br]'
        urlpath = './td[3]/a/@href'
        for row in self.html.xpath(rowpath):
            docket_number = row.xpath(dktpath)
            # Determine the number of urls in each row and pad the docket
            # numbers list sufficiently
            count = len(row.xpath(urlpath))
            docket_numbers.extend(docket_number * count)
        return docket_numbers

    def _get_docket_document_numbers(self):
        document_numbers = []
        regex = re.compile('(\?)(\d+)([a-z]+)(\d+)(-)(.*)')
        for url in self.html.xpath('//table[2]//tr[position()>0]/td[3]/a/@href'):
            # Because we are acting directly on the entire url list, no padding
            # of the docket number field is required.
            doc_no = regex.search(url)
            # In 2012 (and perhaps elsewhere) they have a few weird urls.
            if re.search(regex, url) is not None:
                document_numbers.append(doc_no.group(6))
            else:
                document_numbers.append(url)
        return document_numbers

    def _get_judges(self):
        judges = []
        rowpath = '//table[2]//tr[position()>0]'
        urlpath = './td[3]/a/@href'
        judgepath = './td[3]'
        for row in self.html.xpath(rowpath):
            for judge_element in row.xpath(judgepath):
                judge_string = html.tostring(judge_element, method='text', encoding='unicode')
                judge = re.search('(by\s)(.*)', judge_string, re.MULTILINE).group(2)
                # Determine the number of urls in each row and pad the judges
                # list sufficiently
                count = len(row.xpath(urlpath))
                judges.extend([judge] * count)
        return judges

    def _get_nature_of_suit(self):
        nos = []
        for url in self.html.xpath('//table[2]//tr[position()>0]/td[3]/a/@href'):
            # Because we are acting directly on the entire url list, no padding
            # of the nature of suit field is required.
            regex = '(\?)(\d+)([a-z]+)(\d+)(\-)(.*)'
            url_str = re.search(r'(\?)(\d+)([a-z]+)(\d+)(-)(.*)',url)
            # In 2012 (and perhaps elsewhere) they have a few weird urls.
            if re.search(regex, url) is not None:
                nature_code = url_str.group(3)
                if nature_code == 'cv':
                    nos.append("Civil")
                elif nature_code == 'cr':
                    nos.append("Criminal")
                # This is a tough call. Magistrate Cases are typically also
                # Criminal or Civil cases, and their docket_number field will
                # reflect this, but they do classify these separately under
                # these 'mj' and 'mc' codes and the first page of these
                #  documents will often refer to them as 'Magistrate Case
                # ####-####' so, we will too.
                elif nature_code == 'mj' or 'mc':
                    nos.append("Magistrate Case")
                else:
                    nos.append("Unknown")
            else:
                nos.append("Unknown")
        return nos
