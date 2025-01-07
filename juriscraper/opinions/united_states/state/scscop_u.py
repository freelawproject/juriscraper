from juriscraper.opinions.united_states.state import scscop_p


class Site(scscop_p.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_url = "https://www.sccourts.org/opinions-orders/opinions/unpublished-opinions/supreme-court/"
        self.status = "Unpublished"
    def get_class_name(self):
        return "scscop_u"
