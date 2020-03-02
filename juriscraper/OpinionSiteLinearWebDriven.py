# -*- coding: utf-8 -*-

from juriscraper.OpinionSiteLinear import OpinionSiteLinear
from juriscraper.WebDriven import WebDriven


class OpinionSiteLinearWebDriven(OpinionSiteLinear, WebDriven):
    def __init__(self, *args, **kwargs):
        super(OpinionSiteLinearWebDriven, self).__init__(*args, **kwargs)
        WebDriven.__init__(self, args, kwargs)
