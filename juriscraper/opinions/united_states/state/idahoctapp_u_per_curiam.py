from juriscraper.opinions.united_states.state import idaho_civil


class Site(idaho_civil.Site):
    category = "ICA Unpublished Per Curiam"
    default_status = "Unpublished"
    is_per_curiam = True
