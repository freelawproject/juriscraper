# Auth: mlr
# Date: 2013-05-28

from juriscraper.opinions.united_states.state import hawapp

from datetime import date
from lxml import html


class Site(hawapp.Site):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__

        # If it's the beginning of January, we need to make sure that we aren't
        # missing any late-coming cases from the previous year.
        today = date.today()
        if today.day < 15 and today.month == 1:
            this_year = today.year
            last_year = this_year - 1
            self.url = self.url.replace(str(this_year), str(last_year))
        else:
            # This simply aborts the crawler.
            self.status = 200
            self.html = html.fromstring("<html></html>")
