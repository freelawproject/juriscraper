from juriscraper.opinions.united_states.state import nytrial


class Site(nytrial.Site):
    court_regex = r"^County|(Co(unty?)? Ct)"
