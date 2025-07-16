from datetime import datetime

from juriscraper.opinions.united_states.state import alaska


class Site(alaska.Site):
    # In the Matter of the Suspension of Marcus B Paine v Opinion Number 35
    first_opinion_date = datetime(2000, 6, 30).date()
    is_coa = False
    search_parameter = "PublishedOrders"
    document_type = "PUBORDER"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
