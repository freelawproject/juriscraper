"""Scraper for U.S. Merit Systems Protection Board
CourtID: mspb
Court Short Name: MSPB
Author: Jon Andersen
Reviewer: mlr
Date created: 1 Sep 2014
Type: Non-precedential
History:
    2026-11-01: Read the manifest MSPB's own listing page uses instead of
        the stale _Table.json; add a backscraper.

See mspb_p for how the manifests work. The nonprecedential ones:

- ``NonPrecedentialDecisions_Manifest.json``: loaded by nonprecdec.htm.
  Metadata for every nonprecedential decision, 2007 onward (almost all
  from mid-2010 on). Used for the daily scrape and the backscrape.
- ``NonPrecedentialDecisions_Manifest_Table.json``: what this scraper
  used to read. Nov. 2018 onward; last updated 2026-09-18. It lists 14
  files (issued 2025-03-13 to 2026-01-16) that the full manifest lacks.
- ``NonPrecedentialDecisions_Manifest-updmar2025.json``: loaded by the
  search page; in Nov. 2026 a strict subset of the full manifest.
- ``SEARCH_MANIFESTS/NonPrecedentialDecisions_Manifest_<range>.json``
  (2005-2009, 2010-2014, 2015-2019, 2020-PRESENT, 2022-2024,
  2025-PRESENT): full text for search. Only 2015-2019 holds a file the
  others lack (a redacted 2016 remand order), so it is the only one read.
"""

from datetime import date

from juriscraper.opinions.united_states.administrative_agency import mspb_p


class Site(mspb_p.Site):
    base = "https://www.mspb.gov/decisions/nonprecedential/"
    current_manifest = "NonPrecedentialDecisions_Manifest.json"
    # See mspb_p.Site.backscrape_manifests
    backscrape_manifests: dict[str, tuple[date | None, date | None]] = {
        "NonPrecedentialDecisions_Manifest.json": (None, None),
        "NonPrecedentialDecisions_Manifest_Table.json": (
            date(2018, 11, 30),
            None,
        ),
        "SEARCH_MANIFESTS/NonPrecedentialDecisions_Manifest_2015-2019.json": (
            date(2015, 1, 1),
            date(2019, 12, 31),
        ),
    }
    document_type = "NON-PRECEDENTIAL"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.status = "Unpublished"
