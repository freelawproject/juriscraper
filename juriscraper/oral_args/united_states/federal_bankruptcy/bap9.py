"""Scraper for the Bankruptcy Appellate Panel of the Ninth Circuit
CourtID: bap9
Court Short Name: 9th Cir. BAP
History:
    - 2026-09-22: Created. Reads the `bap` rows of the `ca9` `media` table
      (#2113).

Arguments before 2023 will not match opinion dockets, which had affixes
then, as in `CC-18-1233-LKuF`.
"""

from datetime import datetime

from juriscraper.oral_args.united_states.federal_appellate.ca9 import (
    Site as CA9Site,
)


class Site(CA9Site):
    record_court = "bap9"
    upload_window_days = 90
    first_opinion_date = datetime(2018, 1, 25)
