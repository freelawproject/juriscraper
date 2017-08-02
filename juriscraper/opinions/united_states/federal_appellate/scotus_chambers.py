from juriscraper.opinions.united_states.federal_appellate import scotus_slip


class Site(scotus_slip.Site):

    # Note that scotus_relating inherits from this class.
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.back_scrape_iterable = range(5, int(self.yy) + 1)
        self.precedential = 'In-chambers'
        self.court = 'in-chambers'

    def set_url(self):
        self.url = '%s/%s.aspx' % (self.url_base, self.court)