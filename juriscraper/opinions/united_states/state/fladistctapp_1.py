"""
Scraper for Florida 1st District Court of Appeals
CourtID: fladistctapp1
"""

import re

from juriscraper.lib.string_utils import titlecase
from juriscraper.opinions.united_states.state import fla


class Site(fla.Site):
    # Example built URL
    # "https://flcourts-media.flcourts.gov/_search/opinions/?enddate=2025-12-08&limit=25&offset=0&query=&scopes[]=first_district_court_of_appeal&searchtype=opinions&siteaccess=1dca&startdate=2025-10-01&type[]=pca&type[]=written"
    scopes = "first_district_court_of_appeal"
    site_access = "1dca"
    # Match generic citation including '<vol> <So. reference> <edition> <page>'
    note_citation_regex = re.compile(
        r"(?m)^\d+ *So? *\.? *\dd *\d+(?=\r?$)", re.I
    )

    def get_docket_number(self, raw_docket_number: str) -> str:
        """Prepend the district code to a docket number

        This is useful to disambiguate district court of appeals docket numbers
        See #1136

        :param raw_docket_number: the docket number as returned by the source
        :return: the clean docket number
        """
        court_code = self.site_access[:2].upper()

        if raw_docket_number.startswith(court_code):
            return raw_docket_number

        return f"{court_code}{raw_docket_number.strip()}"

    def get_disposition(self, raw_disposition: str, note: str) -> str:
        """Get a valid disposition value from raw values

        The source has used two schemas over time. Currently, `disposition`
        describes the document ("Appeal - Per Curiam Affirmed") and `note`
        holds the disposition proper ("Affirmed"). In older records the roles
        are reversed: `disposition` holds the disposition ("Reversed") and
        `note` is a continuation clause ("and remanded.") or null. Try the
        modern shape first, then fall back to the older one

        :param raw_disposition: the raw disposition in the returned json
        :param note: a value in the return json that may contain a disposition
        return: A clean disposition value
        """
        valid_dispositions = ("Denied", "Affirmed", "Dismissed", "Reversed")
        if raw_disposition == "Appeal - Per Curiam Affirmed":
            return "Affirmed"

        if note in valid_dispositions:
            return note

        # Split on any whitespace, since a citation may follow the
        # disposition on a new line: "Affirmed\r\n428 So. 3d 1288"
        first_word = (note.split() or [""])[0]
        if first_word in valid_dispositions:
            return first_word

        # Older schema. Keep the whole value, to preserve compound
        # dispositions such as "Affirmed in Part/Reversed in Part"
        if raw_disposition.split(" ")[0] in valid_dispositions:
            return titlecase(raw_disposition)

        return ""

    def get_citation(self, note: str) -> str:
        """Get a citation from the raw note value

        A few months after the publishing of the opinion, a citation is added
        to the `fields.note` string on its own line, usually after the
        disposition. E.g.: 'Affirmed\r\n428 So. 3d 1288'

        Only a line that is entirely a citation is taken, so citations to
        other cases quoted inside longer notes are ignored

        :param note: the raw note value
        :return: the citation, or an empty string
        """
        match = self.note_citation_regex.search(note)
        return match.group() if match else ""
