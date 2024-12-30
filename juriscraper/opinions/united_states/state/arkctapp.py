# Author: Michael Lissner
# Date created: 2013-08-10

import re
from datetime import datetime

from juriscraper.opinions.united_states.state import ark


class Site(ark.Site):
    court_code = "143"
    cite_regex = re.compile(r"\d{2,4} Ark\. App\. \d+", re.I)
    first_opinion_date = datetime(1979, 9, 4)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
