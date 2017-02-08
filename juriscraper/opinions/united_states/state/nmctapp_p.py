from juriscraper.opinions.united_states.state import nm_p

from datetime import date


class Site(nm_p.Site):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        today = date.today()
        self.url = 'http://www.nmcompcomm.us/nmcases/NMARYear.aspx?db=car&y1=%s&y2=%s' % (today.year, today.year)
        self.court_id = self.__module__

    def _download_backwards(self, year):
        self.url = 'http://www.nmcompcomm.us/nmcases/NMARYear.aspx?db=car&y1=%s&y2=%s' % (year, year)
        self.html = self._download()

