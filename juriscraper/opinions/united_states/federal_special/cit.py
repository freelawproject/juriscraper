# Scraper for the United States Court of International Trade
# CourtID: cit
# Court Short Name: Ct. Int'l Trade
# Neutral Citation Format: Ct. Int'l Trade No. 12-1

from juriscraper.OpinionSite import OpinionSite
import time
from datetime import date
from lxml import html


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.url = 'http://www.cit.uscourts.gov/SlipOpinions/index.html'
        self.court_id = self.__module__
        self.base = '//tr[../tr/th[contains(., "Caption")]]'

    def _get_download_urls(self):
        return [t for t in self.html.xpath('{base}/td[1]/a/@href'.format(base=self.base))]

    def _get_neutral_citations(self):
        neutral_citations = []
        for t in self.html.xpath('{base}/td[1]/a/text()'.format(base=self.base)):
            year, item_number = t.split('-')
            neutral_citations.append('20{year} CIT {number}'.format(year=year, number=item_number))
        return neutral_citations

    def _get_case_names(self):
        # Exclude confidential rows by ensuring there is a sibling row that
        # contains an anchor (which confidential cases do not)
        case_names = []
        for e in self.html.xpath('{base}/td[2][../td/a]'.format(base=self.base)):
            text_nodes = e.xpath('.//text()')
            case_names.append(text_nodes[0])
        return case_names

    def _get_precedential_statuses(self):
        statuses = []
        for e in self.html.xpath('{base}/td[2][../td/a]'.format(base=self.base)):
            s = html.tostring(e, method='text', encoding='unicode').lower().strip()
            if "errata" in s:
                statuses.append('Errata')
            else:
                statuses.append('Published')
        return statuses

    def _get_case_dates(self):
        # This does not capture the release dates for the errata documents.
        # The errata release date is listed in column 2. This will use the
        # original release date instead.
        dates = []
        date_formats = ['%m/%d/%Y', '%m/%d/%y']
        for date_string in self.html.xpath('{base}/td[3][../td/a]//text()'.format(base=self.base)):
            for date_format in date_formats:
                try:
                    d = date.fromtimestamp(time.mktime(time.strptime(date_string.strip(), date_format)))
                    dates.append(d)
                    break
                except ValueError:
                    # Try the next format
                    continue
        return dates

    def _get_docket_numbers(self):
        docket_numbers = []
        for e in self.html.xpath('{base}/td[4][../td/a]'.format(base=self.base)):
            docket_numbers.append(html.tostring(e, method='text', encoding='unicode').strip())
        return docket_numbers

    def _get_judges(self):
        judges = []
        for e in self.html.xpath('{base}/td[5][../td/a]'.format(base=self.base)):
            s = html.tostring(e, method='text', encoding='unicode')
            judges.append(s)
        return judges

    def _get_nature_of_suit(self):
        return [t for t in self.html.xpath('{base}/td[6][../td/a]/text()'.format(base=self.base))]
