from juriscraper.opinions.united_states.state import nytrial


class Site(nytrial.Site):
    court_regex = r"Sur{1,}oa?gate|Sur[.r]* Ct"
