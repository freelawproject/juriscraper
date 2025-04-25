from datetime import datetime
import html

from lxml import html
import requests

from casemine.casemine_util import CasemineUtil
from juriscraper.OpinionSiteLinear import OpinionSiteLinear
from juriscraper.opinions.united_states.state import ark_work_comp


class Site(ark_work_comp.Site):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.status = "Published"
        self.court_code = "administrative-law-judge-opinions"

    def get_class_name(self):
        return "ark_admin_law"
