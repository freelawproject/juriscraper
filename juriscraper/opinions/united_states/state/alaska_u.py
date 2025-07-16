from datetime import datetime

from juriscraper.opinions.united_states.state import alaska


class Site(alaska.Site):
    # Charles E. Burnett v Anchorage Refuse, Inc., et al. Opinion Number 846
    first_opinion_date = datetime(1997, 3, 5).date()
    is_coa = False
    search_parameter = "MOJOpinions"
    document_type = "MO&J"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.status = "Unpublished"
        self.is_citation_visible = False
