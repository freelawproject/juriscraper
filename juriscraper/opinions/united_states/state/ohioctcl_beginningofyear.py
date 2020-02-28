# Auth: arderyp
# Date: 2017-01-26

from juriscraper.opinions.united_states.state import ohioctcl

from lxml import html
from datetime import date


class Site(ohioctcl.Site):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__

        # If it's January, we need to make sure that we aren't
        # missing any late-coming cases from the previous year.
        today = date.today()
        if today.month == 1:
            self.year = str(today.year - 1)
        else:
            # This simply aborts the crawler.
            self.status = 200
            self.html = html.fromstring("<html></html>")
