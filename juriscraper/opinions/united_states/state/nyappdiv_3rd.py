# -*- coding: utf-8 -*-
# Scraper for New York Appellate Divisions 3rd Dept.
# CourtID: nyappdiv_3rd
# Court Short Name: NY
# History:
#   2014-07-04: Created by Andrei Chelaru
#   2014-07-05: Reviewed by mlr
#   2014-12-15: Updated to fix regex and insanity errors.
#   2016-02-17: Updated by arderyp, regex was breaking due to new page section.
#   2016-03-08: Updated by arderyp, Added regex back to handle human typos found
#               on older pages, and added fallback loose checking to handle
#               differently formatted disciplinary/admissions docket numbers
#   2016-08-03: Updated by arderyp to handle junk/repetitive anchor tags

import re
import six

from datetime import date
from dateutil.relativedelta import relativedelta, TH

from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.string_utils import clean_if_py3


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        # Last thursday, this court publishes weekly
        self.crawl_date = date.today() + relativedelta(weekday=TH(-1))
        self.url = 'http://decisions.courts.state.ny.us/ad3/CalendarPages/nc{month_nr}{day_nr}{year}.htm'.format(
            month_nr=self.crawl_date.strftime("%m"),
            day_nr=self.crawl_date.strftime("%d"),
            year=self.crawl_date.year
        )
        self.LINK_PATH = "//td[2]//a[contains(./@href, 'Decisions')]"
        self.LINK_HREF_PATH = '%s/@href' % self.LINK_PATH
        self.LINK_TEXT_PATTERN_MEMORANDUM = (r'(?P<docket_number>^\d+((/\d+)+)?)(/)?'
                                             r'(?P<case_name>.+)')
        self.LINK_TEXT_PATTERN_ATTORNEY = (r'(?P<docket_number>^\w{1}-\d+-\d+)'
                                          r'(?P<case_name>.+)')

    def _get_case_names(self):
        case_names = []
        for link in self.html.xpath(self.LINK_PATH):
            text = link.text_content().strip()
            if text:
                docket, name = self._get_docket_and_name_from_text(text)
                if name:
                    case_names.append(name)
        return case_names

    def _get_download_urls(self):
        urls = []
        for link in self.html.xpath(self.LINK_PATH):
            if link.text_content().strip():
                urls.append(link.xpath('@href')[0])
        return urls

    def _get_case_dates(self):
        return [self.crawl_date] * len(self._get_case_names())

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_names)

    def _get_docket_numbers(self):
        docket_numbers = []
        for link in self.html.xpath(self.LINK_PATH):
            text = link.text_content().strip()
            if text:
                docket, name = self._get_docket_and_name_from_text(text)
                if docket:
                    docket_numbers.append(docket)
        return docket_numbers

    def _get_docket_and_name_from_text(self, text):
        text = self._sanitize_docket_name_text(text)
        if not text:
            return False, False
        if text.split()[0].count('-') == 2:
            regex = self.LINK_TEXT_PATTERN_ATTORNEY
        else:
            regex = self.LINK_TEXT_PATTERN_MEMORANDUM
        data = re.search(regex, text)
        docket_raw = data.group('docket_number')
        docket = ', '.join(docket_raw.split('/'))
        name = ' '.join(data.group('case_name').split())

        return docket, name

    def _sanitize_docket_name_text(self, text):
        text = clean_if_py3(text).strip()
        first_word = text.split()[0]

        # Replace en dash typo with proper hyphen so regex parses properly
        en_dash = b'\xe2\x80\x93'.decode('utf-8')
        first_word_sanitized = first_word.replace(en_dash, '-')

        return text.replace(first_word, first_word_sanitized)
