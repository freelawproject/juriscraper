# Author: Michael Lissner
# Date created: 2013-06-21

import datetime

from juriscraper.opinions.united_states.state import wva


class Site(wva.Site):
    first_opinion_date = datetime.date(2022, 1, 1)
    opinions_path = "/appellate-courts/intermediate-court-of-appeals/opinions"
    prior_terms_path = (
        "/appellate-courts/intermediate-court-of-appeals/opinions/prior-terms"
    )
    year_param = "field_ica_opinion_year_value"
