from juriscraper.opinions.united_states.state import calctapp_new


class Site(calctapp_new.Site):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_status="Unpublished"
        self.set_url_keyword="unpublishednon-citable-opinions"
        self.pattern = r'(CA\d+(?:/\d+)?)'
        self.opn_type = "Opinion"

    def get_class_name(self):
        return "calctapp_new_u"