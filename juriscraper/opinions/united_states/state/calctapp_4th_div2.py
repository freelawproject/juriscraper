# Scraper for California's Fourth District Court of Appeal Division 2
# CourtID: calctapp_4th_div2
# Court Short Name: Cal. Ct. App.

from juriscraper.opinions.united_states.state import calctapp_1st


class Site(calctapp_1st.Site):
    court_code = "E"
    division = "4th App. Dist. Div. 2"
