from datetime import datetime

from . import alaska


class Site(alaska.Site):
    # Clarence Kameroff v State of Alaska. Opinion Number 1488
    first_opinion_date = datetime(1996, 10, 11).date()
    is_coa = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
