# Author: Michael Lissner
# Date created: 2013-06-11
# This court only hears cases that the ND Supreme Court assigns to it. As a
# result, years can go by without a case from this court.


from juriscraper.opinions.united_states.state import nd

from datetime import date
from datetime import datetime
from lxml import html


class Site(nd.Site):
    def __init__(self):
        super(Site, self).__init__()
        self.court_id = self.__module__
        today = date.today()
        now = datetime.now()
        self.url = 'http://www.ndcourts.gov/opinions/month/%s.htm' % (today.strftime("%b%Y"))
        if today.day == 1 and now.hour < 16:
            # On the first of the month, the page doesn't exist until later in the day, so when that's the case,
            # we don't do anything until after 16:00. If we try anyway, we get a 503 error. This simply aborts the
            # crawler.
            self.status = 200
            self.html = html.fromstring('<html></html>')

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
