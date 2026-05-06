from juriscraper.opinions.united_states.state import idaho_civil


class Site(idaho_civil.Site):
    category = "ICA Unpublished"
    default_status = "Unpublished"
    page_size = 20
