from juriscraper.opinions.united_states.state import nytrial


class Site(nytrial.Site):
    court_regex = r"^Ct Cl|C(our)?t( [Oo]f)? Cl(aims)?$"
