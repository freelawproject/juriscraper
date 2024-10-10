from importlib import import_module

# `or` is a python reserved keyword; can't import the module as usual
oregon_module = import_module("juriscraper.opinions.united_states.state.or")


class Site(oregon_module.Site):
    court_code = "p17027coll6"
    days_interval = 120
