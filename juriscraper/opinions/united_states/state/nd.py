# Author: Michael Lissner
# Date created: 2013-06-06
# History:
#   2013-07-01, mlr: make it abort on 1st of month before 4pm
#   2017-02-08, mlr: Add a backscraper

import re
from dateutil.rrule import rrule, MONTHLY
from lxml import html
from datetime import date
from datetime import datetime

from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.string_utils import convert_date_string


class Site(OpinionSite):
    """This will scrape all cases, excluding Appeal
    cases from the ND court site
    """

    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        today = date.today()
        now = datetime.now()
        self.url = 'https://www.ndcourts.gov/opinions/month/%s.htm' % (today.strftime("%b%Y"))
        if today.day == 1 and now.hour < 16:
            # On the first of the month, the page doesn't exist until later in
            # the day, so when that's the case, we don't do anything until after
            # 16:00. If we try anyway, we get a 503 error. This simply aborts
            # the crawler.
            self.status = 200
            self.html = html.fromstring('<html></html>')
        self.back_scrape_iterable = [i.date() for i in rrule(
            MONTHLY,
            dtstart=date(1998, 10, 1),
            until=date(2017, 1, 1),
        )]

    def _get_cases_from_page(self):
        cases = []
        if not self.html.xpath('//body/a'):
            # Exit early for months with no cases (January 2009)
            return cases
        case_date = None
        citation_pattern = '^.{0,5}(\d{4} ND (?:App )?\d{1,4})'
        for element in self.html.xpath('//body/a|//body/font|//body/text()'):
            if hasattr(element, 'tag'):
                if element.tag == 'font' and element.text:
                    case_date = convert_date_string(element.text)
                elif element.tag == 'a' and case_date:
                    name = element.xpath('text()')[0].strip()
                    url = element.xpath('@href')[0]
                    docket = url.split('/')[-1].split('.')[0]
            else:
                # Clean up text to make sure only single spaces between words
                # to ensure that regex pattern works even if clerk accidentally
                # types a tab or multiple spaces
                text = ' '.join(element.strip().split())
                found_citation = re.search(citation_pattern, text, re.MULTILINE)
                if found_citation and found_citation.group(1):
                    citation = found_citation.group(1)
                    if self._should_scrape_case(citation) and name and case_date and docket:
                        cases.append({
                            'citation': citation,
                            'name': name,
                            'date': case_date,
                            'download': 'http://www.ndcourts.gov/wp/%s.wpd' % docket,
                            'docket': docket
                        })
        return cases

    @staticmethod
    def _is_appellate_citation(citation):
        return ' App ' in citation

    def _should_scrape_case(self, citation):
        return not self._is_appellate_citation(citation)

    def _get_download_urls(self):
        return [case['download'] for case in self._get_cases_from_page()]

    def _get_case_names(self):
        return [case['name'] for case in self._get_cases_from_page()]

    def _get_case_dates(self):
        return [case['date'] for case in self._get_cases_from_page()]

    def _get_docket_numbers(self):
        return [case['docket'] for case in self._get_cases_from_page()]

    def _get_neutral_citations(self):
        return [case['citation'] for case in self._get_cases_from_page()]

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_names)

    def _download_backwards(self, d):
        """This should provide """
        self.url = self.url = 'https://www.ndcourts.gov/opinions/month/%s.htm' % (d.strftime("%b%Y"))
        self.html = self._download()
