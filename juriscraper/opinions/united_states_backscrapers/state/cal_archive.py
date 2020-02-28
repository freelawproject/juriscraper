from juriscraper.opinions.united_states.state import cal


class Site(cal.Site):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.url = (
            "http://www.courtinfo.ca.gov/cgi-bin/opinarch-blank.cgi?Courts=S"
        )
        self.court_id = self.__module__
