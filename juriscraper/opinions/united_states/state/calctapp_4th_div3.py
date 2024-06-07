# Scraper for California's Fourth District Court of Appeal Division 3
# CourtID: calctapp_4th_div3
# Court Short Name: Cal. Ct. App.

from juriscraper.opinions.united_states.state import calctapp_1st


class Site(calctapp_1st.Site):
    court_code = "G"
    division = "4th App. Dist. Div. 3"
