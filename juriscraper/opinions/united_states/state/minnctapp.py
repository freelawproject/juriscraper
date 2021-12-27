# Scraper for Minnesota Court of Appeals Published Opinions
# CourtID: minnctapp
# Court Short Name: MN
# Author: mlr
# Date: 2016-06-03


from juriscraper.opinions.united_states.state import minn


class Site(minn.Site):
    # Only subclasses minn for the _download method.
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.court_filters = ["/ctapun/", "/ctappub/"]
