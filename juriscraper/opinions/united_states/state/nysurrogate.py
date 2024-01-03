from juriscraper.opinions.united_states.state import nymisc


class Site(nymisc.Site):
    court_regex = r"^Surrogate"
