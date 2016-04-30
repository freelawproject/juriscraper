#Scraper for Minnesota Court of Appeals Published Opinions
#CourtID: minnctapp
#Court Short Name: MN
#Author: Andrei Chelaru
#Reviewer: mlr
#Date: 2014-07-03

from juriscraper.opinions.united_states.state import minn


class Site(minn.Site):
    court_abbreviation = 'ctappub'

