# Author: Michael Lissner
# Date created: 2013-06-11

from datetime import date
from juriscraper.opinions.united_states_backscrapers.state import nd


class Site(nd.Site):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        today = date.today()
        self.url = 'http://www.ndcourts.gov/opinions/month/%s.htm' % (today.strftime("%b%Y"))

    def _post_parse(self):
        # Remove any information that applies to non-appellate cases.
        if self.neutral_citations:
            delete_items = []
            for i in range(0, len(self.neutral_citations)):
                if 'App' not in self.neutral_citations[i]:
                    delete_items.append(i)

            for i in sorted(delete_items, reverse=True):
                del self.download_urls[i]
                del self.case_names[i]
                del self.case_dates[i]
                del self.precedential_statuses[i]
                del self.docket_numbers[i]
                del self.neutral_citations[i]
        else:
            # When there aren't any neutral cites that means everything is a supreme court case, and it all gets
            # deleted.
            self.download_urls = []
            self.case_names = []
            self.case_dates = []
            self.precedential_statuses = []
            self.docket_numbers = []
            self.neutral_citations = []

    def _download_backwards(self, d):
        self.crawl_date = d
        self.url = 'http://www.ndcourts.gov/opinions/month/%s.htm' % (d.strftime("%b%Y"))
        self.html = self._download()
