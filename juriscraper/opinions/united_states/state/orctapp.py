"""
Scraper for Oregon Court of Appeals
CourtID: orctapp
Court Short Name: OR Ct App
Author: William Palin
History:
    - 2023-11-18: Created
"""

from importlib import import_module

# `or` is a python reserved keyword; can't import the module as usual
oregon_module = import_module("juriscraper.opinions.united_states.state.or")


class Site(oregon_module.Site):
    court_code = "p17027coll5"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
