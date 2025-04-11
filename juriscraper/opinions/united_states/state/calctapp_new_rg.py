from juriscraper.opinions.united_states.state import calctapp_new


class Site(calctapp_new.Site):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_status="Published"
        self.set_url_keyword="published-opinions-review-granted"
        self.pattern = r'\b\d{1,2}/\d{1,2}/\d{2,4}\b'
        self.opn_type="Review Granted"

    def get_class_name(self):
        return "calctapp_new_rg"