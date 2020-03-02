# -*- coding: utf-8 -*-

from juriscraper.OpinionSite import OpinionSite
from juriscraper.WebDriven import WebDriven


class OpinionSiteWebDriven(OpinionSite, WebDriven):
    def __init__(self, *args, **kwargs):
        super(OpinionSiteWebDriven, self).__init__(*args, **kwargs)
        WebDriven.__init__(self, args, kwargs)
