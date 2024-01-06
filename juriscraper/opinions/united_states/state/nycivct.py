from juriscraper.opinions.united_states.state import nytrial


class Site(nytrial.Site):
    court_regex = r"Civ(il)? C[our]*t|[HC]CIV|Hous Part"
