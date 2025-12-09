"""
Scraper for Florida 1st District Court of Appeals
CourtID: fladistctapp1
"""

from juriscraper.opinions.united_states.state import fla


class Site(fla.Site):
    # Example built URL
    # "https://flcourts-media.flcourts.gov/_search/opinions/?enddate=2025-12-08&limit=25&offset=0&query=&scopes[]=first_district_court_of_appeal&searchtype=opinions&siteaccess=1dca&startdate=2025-10-01&type[]=pca&type[]=written"
    scopes = "first_district_court_of_appeal"
    site_access = "1dca"

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

        :param raw_disposition: the raw disposition in the returned json
        :param note: a value in the return json that may contain a disposition
        return: A clean disposition value
        """
        valid_dispositions = ("Denied", "Affirmed", "Dismissed", "Reversed")
        if raw_disposition == "Appeal - Per Curiam Affirmed":
            return "Affirmed"

        if (
            note in valid_dispositions
            or note.split(" ")[0] in valid_dispositions
        ):
            return note.split(" ")[0]

        return ""
