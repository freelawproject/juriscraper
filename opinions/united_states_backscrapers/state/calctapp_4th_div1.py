# Backscraper Scraper for California's Fourth District Court of Appeal Division 1
# CourtID: calctapp_4th_div1
# Court Short Name: Cal. Ct. App.
# Author: Andrei Chelaru
from datetime import date
from dateutil.rrule import DAILY, rrule
from juriscraper.opinions.united_states_backscrapers.state import calctapp_1st


class Site(calctapp_1st.Site):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.district = 41
        self.court_id = self.__module__

        self.back_scrape_iterable = [i.date() for i in rrule(
            DAILY,
            interval=self.interval,
            dtstart=date(2007, 5, 1),
            until=date(2016, 1, 1),
        )]