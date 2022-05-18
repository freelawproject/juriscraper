"""
CourtID: illappct
Court Short Name: Ill. App. Ct.
Author: Rebecca Fordon
Reviewer: Mike Lissner
History:
* 2016-06-23: Created by Rebecca Fordon
* 2022-05-18: Updated by William E. Palin
"""

from juriscraper.oral_args.united_states.state import illappct_1st_dist


class Site(illappct_1st_dist.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.district = "WC"
        self._set_parameters()
