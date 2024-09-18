from datetime import date

from juriscraper.opinions.united_states.state import sc


class Site(sc.Site):
    court = "court-of-appeals"
    opinion_status = "unpublished-opinions"
    first_opinion_date = date(2003, 1, 1)
