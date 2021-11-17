from . import alaska


class Site(alaska.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "https://appellate-records.courts.alaska.gov/CMSPublic/Home/Opinions?isCOA=True"
