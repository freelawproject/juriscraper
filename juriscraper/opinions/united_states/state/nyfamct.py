from juriscraper.opinions.united_states.state import nytrial


class Site(nytrial.Site):
    court_regex = r"Fam Ct|Family Court|Youth Part"
