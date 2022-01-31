"""Scraper for Colorado Appeals Court
CourtID: coloctapp
Court Short Name: Colo. Ct. App.

History:
    - 2022-01-31: Updated by William E. Palin
"""

from juriscraper.lib.string_utils import convert_date_string
from juriscraper.opinions.united_states.state import colo


class Site(colo.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "https://www.courts.state.co.us/Courts/Court_of_Appeals/Case_Announcements/"

    def _process_html(self) -> None:
        """Process the HTML

        This is an odd little site, where they just post unpublished and published opinions without links.
        Fortunately, its easy enough to crawl and the pattern for the URLs is pretty consistent. (i think)

        The URL looks like this https://www.courts.state.co.us/Courts/Court_of_Appeals/Opinion/[YEAR]/[DOCKET]-[PD].pdf

        I think PD means Published Decision, but I'm not sure.  If it is then the URLs should work everytime.
        The caveat is that the Supreme Court seems to have some lag between switching to 2022 from 2021 bucket but
        the URLS are given there.

        :return: None
        """
        rows = self.html.xpath("//p")
        date = rows[0].text_content()
        date_year = convert_date_string(date)

        if "P U B L I S H E D  O P I N I O N S" != rows[1].text_content():
            return {}
        for row in rows[2:]:
            if row.text_content() == "U N P U B L I S H E D  O P I N I O N S":
                break
            row_text = row.text_content().strip()
            docket, name = row_text.split(" ", 1)
            self.cases.append(
                {
                    "date": date,
                    "docket": docket,
                    "name": name,
                    "url": f"https://www.courts.state.co.us/Courts/Court_of_Appeals/Opinion/{date_year.year}/{docket}-PD.pdf",
                    "status": "Published",
                }
            )
