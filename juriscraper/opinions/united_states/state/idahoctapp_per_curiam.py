from datetime import datetime
from time import strftime

from casemine.casemine_util import CasemineUtil
from juriscraper.lib.exceptions import InsanityException
from juriscraper.lib.string_utils import clean_string, convert_date_string
from juriscraper.OpinionSiteLinear import OpinionSiteLinear
from juriscraper.opinions.united_states.state import idahoctapp_u


class Site(idahoctapp_u.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "https://isc.idaho.gov/appeals-court/Unpublished-Per-Curiam"

    def get_class_name(self):
        return "idahoctapp_per_curiam"
