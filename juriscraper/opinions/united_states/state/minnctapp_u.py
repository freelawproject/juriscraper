# Scraper for Minnesota Court of Appeals Unpublished Opinions
# CourtID: minnctapp_u
# Court Short Name: Minn Ct App
# Author: mlr
# Date: 2016-06-03


from . import minn


class Site(minn.Site):
    court_query = "ctapun"

    def get_class_name(self):
        return "minnctapp_u"

    def get_court_name(self):
        return "Minnesota Court of Appeals"
