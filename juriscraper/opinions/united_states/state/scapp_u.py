from juriscraper.opinions.united_states.state import scscop_p


class Site(scscop_p.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_url = "https://www.sccourts.org/opinions-orders/opinions/unpublished-opinions/court-of-appeals/"
        self.status = "Unpublished"

    def get_class_name(self):
        return "scapp_u"

    def get_court_name(self):
        return "South Carolina Court of Appeals"
