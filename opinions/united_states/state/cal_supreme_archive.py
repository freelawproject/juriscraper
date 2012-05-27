import ca_supreme


class Site(ca_supreme.Site):
    def __init__(self):
        super(Site, self).__init__()
        self.url = (
        'http://www.courtinfo.ca.gov/cgi-bin/opinarch-blank.cgi?Courts=S')
        self.court_id = self.__module__
