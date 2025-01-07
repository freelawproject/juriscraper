from juriscraper.opinions.united_states.state import neb_sup_all_op


class Site(neb_sup_all_op.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = (
            "https://www.nebraska.gov/apps-courts-epub/public/appeals"
        )

    def get_class_name(self):
        return "neb_ctapp_all_op"

    def get_court_name(self):
        return "Nebraska Court of Appeals"
