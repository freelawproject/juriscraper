"""Scraper for the Rhode Island Supreme Court
CourtID: ri
Court Short Name: R.I.
Court Contact: helpdesk@courts.ri.gov, MFerris@courts.ri.gov (Ferris, Mirella), webmaster@courts.ri.gov
    https://www.courts.ri.gov/PDF/TelephoneDirectory.pdf
Author: Brian W. Carver
Date created: 2013-08-10
"""

import re
from datetime import datetime

from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.exceptions import InsanityException
from juriscraper.lib.string_utils import convert_date_string


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.base_url = 'http://www.courts.ri.gov/Courts/SupremeCourt/Pages/Opinions/Opinions'
        self.url = self.build_url()
        self.cases = []
        self.previous_date = None
        self.include_summary = True
        self.precedential_status = 'Published'

    def build_url(self):
        # This court hears things from mid-September to end of June. This
        # defines the "term" for that year, which triggers the website updates.
        today = datetime.today()
        if today >= datetime(today.year, 9, 15):
            year = today.year
        else:
            year = today.year - 1
        return '%s%d-%d.aspx' % (self.base_url, year, year + 1)

    def _download(self, request_dict={}):
        # Site has non-chained, bad certificate, need to
        # ignore ssl verification for now for scraper to work
        request_dict['verify'] = False
        html = super(Site, self)._download(request_dict)
        self.extract_cases_from_html(html)
        return html

    def extract_cases_from_html(self, html):
        # case information spans over 3 rows, so must process 3 at a time:
        #   <tr> - contains case name, docket number, date and pdf link
        #   <tr> - contains case summary
        #   <tr> - contains a one-pixel gif spacer
        table = "//table[@id = 'onetidDoclibViewTbl0']/tr[position() > 1]"
        rows = list(html.xpath(table))
        row_triplets = list(zip(rows, rows[1:]))[::3]

        for tr1, tr2 in row_triplets:
            case = self.extract_case_from_rows(tr1, tr2)
            self.previous_date = case['date']
            self.cases.append(case)

    def extract_case_from_rows(self, row1, row2):
        docket = row1.xpath('./td/a/text()')[0]
        docket = ', '.join([d.strip() for d in docket.split(',')])
        url = row1.xpath("./td/a/@href")[0]
        text = row1.xpath("./td[1]/text()")[0]
        text_to_parse = [text]

        if self.include_summary:
            summary_lines = row2.xpath("./td/div/text()")
            summary = '\n'.join(summary_lines)
            joined_text = '\n'.join([text, summary_lines[0]])
            text_to_parse.append(joined_text)
        else:
            summary = False

        return {
            'url': url,
            'docket': docket,
            'date': self.parse_date_from_text(text_to_parse),
            'name': self.parse_name_from_text(text_to_parse),
            'summary': summary,
        }

    def parse_date_from_text(self, text_list):
        regex = '(.*?)(\((\w+\s+\d+\,\s+\d+)\))(.*?)'
        for text in text_list:
            date_match = re.match(regex, text)
            if date_match:
                return convert_date_string(date_match.group(3))

        # Fall back on previous case's date
        if self.previous_date:
            return self.previous_date

        raise InsanityException('Could not parse date from string, and no '
                                'previous date to fall back on: "%s"' %
                                text_list)

    @staticmethod
    def parse_name_from_text(text_list):
        regexes = [
            # Expected format
            '(.*?)(,?\sNos?\.)(.*?)',
            # Clerk typo, forgot "No."/"Nos." substring
            '(.*?)(,?\s\d+-\d+(,|\s))(.*?)',
            # Same as above, and there's an unconventional docket number
            # like 'SU-14-324' instead of '14-324'. See ri_p_example_4.html
            '(.*?)(,?\s(?:\w+-)?\d+-\d+(,|\s))(.*?)',
        ]

        for regex in regexes:
            for text in text_list:
                name_match = re.match(regex, text)
                if name_match:
                    return name_match.group(1)

        # "No."/"Nos." and docket missing, fall back on whatever's before first
        # semi-colon
        for text in text_list:
            if ';' in text:
                return text.split(';')[0]

        raise InsanityException('Could not parse name from string: "%s"' %
                                text_list)

    def _get_case_names(self):
        return [case['name'] for case in self.cases]

    def _get_download_urls(self):
        return [case['url'] for case in self.cases]

    def _get_case_dates(self):
        return [case['date'] for case in self.cases]

    def _get_precedential_statuses(self):
        return [self.precedential_status] * len(self.cases)

    def _get_docket_numbers(self):
        return [case['docket'] for case in self.cases]

    def _get_summaries(self):
        return [case['summary'] for case in self.cases]
