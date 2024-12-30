from juriscraper.opinions.united_states.state import nytrial


class Site(nytrial.Site):
    court_regex = r"City? (Ct|Court)"
    # Most start with the regex, but there are special cases
    # such as 'Utica City Ct' in Dec 2023
