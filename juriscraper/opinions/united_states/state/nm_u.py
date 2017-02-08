from juriscraper.opinions.united_states.state import nm_p

from datetime import date

class Site(nm_p.Site):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        today = date.today()
        self.url = 'http://www.nmcompcomm.us/nmcases/NMUnrepYear.aspx?db=scu&y1=%s&y2=%s' % (today.year, today.year)
        self.court_id = self.__module__

    def _get_docket_numbers(self):
        path = '//table[@id="GridView1"]/tr/td[3]//text()'
        return list(self.html.xpath(path))

    def _get_neutral_citations(self):
        return None

    def _get_precedential_statuses(self):
        return ["Unpublished"] * len(self.case_names)

    def _download_backwards(self, year):
        self.url = 'http://www.nmcompcomm.us/nmcases/NMUnrepYear.aspx?db=scu&y=%s' % year
        self.html = self._download()


