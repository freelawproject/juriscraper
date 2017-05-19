"""Scraper for North Carolina Supreme Court
CourtID: nc
Court Short Name: N.C.
Reviewer:
History:
    2014-05-01: Created by Brian Carver
    2014-08-04: Rewritten by Jon Andersen with complete backscraper
"""

import re
from datetime import date
from datetime import datetime
import traceback

from juriscraper.OpinionSite import OpinionSite
from lxml import html

from juriscraper.lib.exceptions import InsanityException


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = 'http://appellate.nccourts.org/opinions/?c=sc&year=%s' % date.today().year
        self.back_scrape_iterable = range((date.today().year - 1), 1997, -1)
        self.my_download_urls = []
        self.my_case_names = []
        self.my_docket_numbers = []
        self.my_summaries = []
        self.my_neutral_citations = []
        self.my_precedential_statuses = []

    def _get_case_dates(self):
        case_dates = []
        case_date = None
        precedential_status = "Published"
        date_cleaner = "\d+ \w+ [12][90]\d\d"
        path = '//table//tr'
        for row_el in self.html.xpath(path):
            # Examine each row. If it contains the date, we set that as
            # the current date. If it contains a case, we parse it.
            try:
                date_nodes = row_el.xpath('.//strong/text()')
                date_str = date_nodes[0]
                if date_nodes:
                    date_str = re.search(date_cleaner,
                                         date_str, re.MULTILINE).group()
                    case_date = datetime.strptime(date_str, '%d %B %Y').date()
                    # When a new date header appears, switch to Precedential
                    precedential_status = "Published"
                    continue  # Row contained just the date, move on
            except IndexError:
                # No matching nodes; not a date header
                pass

            path = "./td[contains(., 'Unpublished Opinions - Rule 30e')]"
            if row_el.xpath(path):
                precedential_status = "Unpublished"
                # When this header appears, switch to Nonprecedential, then
                # press on to the following rows.
                continue

            if precedential_status == "Published":
                urls = row_el.xpath('./td/span/span[1]/@onclick')
                # Like: viewOpinion("http://appellate.nccourts.org/opinions/?c=1&amp;pdf=31511")
                if len(urls) != 1 or urls[0].find('viewOpinion') != 0:
                    continue  # Only interested in cases with a download link

                # Pull the URL out of the javascript viewOpinion function.
                download_url = re.search(
                    'viewopinion\("(.*)"',
                    urls[0],
                    re.IGNORECASE
                ).group(1)

                path = "./td/span/span[contains(@class,'title')]"
                txt = html.tostring(row_el.xpath(path)[0],
                                    method='text',
                                    encoding='unicode')
                case_name, neutral_cite, docket_number = self.parse_title(txt)

                summary = ""
                path = "./td/span/span[contains(@class,'desc')]/text()"
                summaries = row_el.xpath(path)
                try:
                    summary = summaries[0]
                except IndexError:
                    # Not all cases have a summary
                    pass
                if case_name.strip() == "":
                    continue  # A few cases are missing a name

                case_dates.append(case_date)
                self.my_download_urls.append(download_url)
                self.my_case_names.append(case_name)
                self.my_docket_numbers.append(docket_number)
                self.my_summaries.append(summary)
                self.my_neutral_citations.append(neutral_cite)
                self.my_precedential_statuses.append(precedential_status)

            elif precedential_status == "Unpublished":
                for span in row_el.xpath('./td/span'):
                    if 'onclick' not in span.attrib.keys():
                        continue
                    download_url = re.search('viewopinion\("(.*)"',
                                             span.attrib['onclick'],
                                             re.IGNORECASE).group(1)

                    txt = span.text_content().strip()
                    (case_name, neutral_cite, docket_number) = self.parse_title(txt)
                    if case_name.strip() == "":
                        continue  # A few cases are missing a name
                    case_dates.append(case_date)
                    self.my_download_urls.append(download_url)
                    self.my_case_names.append(case_name)
                    self.my_docket_numbers.append(docket_number)
                    self.my_summaries.append("")
                    self.my_neutral_citations.append(neutral_cite)
                    self.my_precedential_statuses.append(precedential_status)

        return case_dates

    # Parses case titles like:
    # Fields v. Harnett Cnty., 367 NC 12 (13-761)
    # Clark v. Clark,  (13-612)
    @staticmethod
    def parse_title(txt):
        try:
            name_and_citation = txt.rsplit('(', 1)[0].strip()
            docket_number = re.search('(.*\d).*?',
                                      txt.rsplit('(', 1)[1]).group(0).strip()
            case_name = name_and_citation.rsplit(",", 1)[0].strip()
            try:
                neutral_cite = name_and_citation.rsplit(",", 1)[1].strip()
                if not re.search('^\d\d.*\d\d$', neutral_cite):
                    neutral_cite = ''
            except IndexError:
                # Unable to find comma to split on. No neutral cite.
                neutral_cite = ''
        except:
            raise InsanityException("Unable to parse: %s\n%s" %
                                    (txt, traceback.format_exc()))
        return case_name, neutral_cite, docket_number

    def _get_download_urls(self):
        return self.my_download_urls

    def _get_case_names(self):
        return self.my_case_names

    def _get_docket_numbers(self):
        return self.my_docket_numbers

    def _get_summaries(self):
        return self.my_summaries

    def _get_neutral_citations(self):
        return self.my_neutral_citations

    def _get_precedential_statuses(self):
        return self.my_precedential_statuses

    def _download_backwards(self, year):
        self.url = 'http://appellate.nccourts.org/opinions/?c=sc&year=%s' % year
        self.html = self._download()
