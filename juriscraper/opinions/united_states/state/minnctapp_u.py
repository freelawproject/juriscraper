# Scraper for Minnesota Court of Appeals Unpublished Opinions
# CourtID: minnctapp_u
# Court Short Name: Minn Ct App
# Author: mlr
# Date: 2016-06-03


from . import minn


class Site(minn.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.parameters = {
            "v:sources": "mn-law-library-opinions",
            "query": " (url:/archive/ctapun) ",
            "sortby": "date",
        }
        self.status = "Unpublished"
