from juriscraper.opinions.united_states.state import nytrial


class Site(nytrial.Site):
    court_regex = r"(Just|Village|Town) Ct|Just(ice)? Cour+t"
