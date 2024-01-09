from juriscraper.opinions.united_states.state import nytrial


class Site(nytrial.Site):
    court_regex = r"Cri?m(inal)? C[our]*t"
