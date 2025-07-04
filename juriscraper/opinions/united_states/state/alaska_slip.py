from datetime import datetime

from juriscraper.opinions.united_states.state import alaska


class Site(alaska.Site):
    # In the Matter of the Suspension of Marcus B Paine v Opinion Number 35
    first_opinion_date = datetime(2000, 6, 30).date()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "https://appellate-records.courts.alaska.gov/CMSPublic/Home/PublishedOrders?isCOA=False"
