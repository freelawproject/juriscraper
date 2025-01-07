from juriscraper.opinions.united_states.state import scscop_p


class Site(scscop_p.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_url = "https://www.sccourts.org/opinions-orders/opinions/published-opinions/court-of-appeals/"
        self.status = "Published"

    def get_class_name(self):
        return "scapp_p"

    def get_court_name(self):
        return "South Carolina Court of Appeals"
