# Author: Michael Lissner
# Date created: 2013-06-21

from datetime import date

from juriscraper.opinions.united_states.state import neb


class Site(neb.Site):
    backscrape_url = "https://www.nebraska.gov/apps-courts-epub/public/appeals"
    # opening date of 16 Neb. App., first volume with an opinions list
    first_opinion_date = date(2007, 10, 9)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = (
            "https://supremecourt.nebraska.gov/courts/court-appeals/opinions"
        )
