from juriscraper.opinions.united_states.state import nymisc


class Site(nymisc.Site):
    court_regex = r"City Ct"
    # Most start with the regex, but there are special cases
    # such as 'Utica City Ct' in Dec 2023
