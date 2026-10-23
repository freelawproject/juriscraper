"""Scraper for unpublished dispositions of the Nevada Supreme Court
CourtID: nev
Court Short Name: Nev.

History:
    - 2026-07-11: Created, #2011
"""

import re
from datetime import datetime

from juriscraper.opinions.united_states.state import nev


class Site(nev.Site):
    # "Order/Dispositional" docket entries: unpublished dispositions such
    # as "Order of Affirmance", "Order Dismissing Appeal" or "Order
    # Denying Petition". Under NRAP 36(c)(3) these are citable for their
    # persuasive value when entered on or after 2016-01-01 (Supreme
    # Court) or 2024-08-15 (Court of Appeals)
    opinion_type_id = "1000018"

    # Earliest "Order/Dispositional" entry in the ACIS feed
    first_opinion_date = datetime(1999, 8, 10)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.status = "Unpublished"

    def parse_description(self, description: str) -> dict:
        """Extract metadata from an unpublished order's description

        Unpublished orders have no Advance Opinion citation, and their
        disposition is the leading phrase (e.g. "Order of Affirmance",
        often prefixed "Filed Order of Affirmance") rather than the
        quoted boilerplate ("ORDER the judgment of the district court
        AFFIRMED."), which is inconsistently quoted. The trailing
        initials (e.g. "KP/RP/LB") are panel initials, not surnames, so
        the parent's judge extraction stays empty.

        :param description: the free-text docketEntryDescription
        :return: dict with citation, disposition, author, per_curiam and judge
        """
        metadata = super().parse_description(description)
        first_sentence = description.split(".", 1)[0].strip()
        first_sentence = re.sub(r"^Filed\s+", "", first_sentence)
        if first_sentence:
            metadata["disposition"] = first_sentence
        return metadata
