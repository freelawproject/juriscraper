# Scraper for Minnesota Court of Appeals Published Opinions
# CourtID: minnctapp_p
# Court Short Name: Minn Ct App
# Author: mlr
# Date: 2016-06-03

from . import minn


class Site(minn.Site):
    court_query = "ctappub"
