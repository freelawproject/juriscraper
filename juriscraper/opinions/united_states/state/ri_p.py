"""Scraper for the Rhode Island Supreme Court
CourtID: ri
Court Short Name: R.I.
Court Contact: helpdesk@courts.ri.gov, MFerris@courts.ri.gov (Ferris, Mirella), webmaster@courts.ri.gov
    https://www.courts.ri.gov/PDF/TelephoneDirectory.pdf
Author: Brian W. Carver
Date created: 2013-08-10
History:
    Date created: 2013-08-10 by Brian W. Carver
    2022-05-02: Updated by William E. Palin, to use JSON responses
"""
from datetime import datetime

from lxml import html

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.status = "Published"
        self.opinion_type = "Opinions"
        self.url = self.build_url()

    def _download(self, request_dict={}):
        if self.test_mode_enabled():
            self.json = super()._download(request_dict)
            return
        return super()._download(request_dict)

    def fetch_json(self) -> None:
        """Fetch JSON data from the site.

        :return: None
        """
        if self.test_mode_enabled():
            return
        content = html.tostring(self.html)
        self.request["parameters"] = {
            "params": {
                "List": content.split(b"ctx.listName ")[1].split(b'"')[1],
                "View": content.split(b"ctx.view ")[1].split(b'"')[1],
                "ViewCount": 310,
                "IsXslView": "TRUE",
                "IsCSR": "TRUE",
            }
        }
        self._request_url_post(
            "https://www.courts.ri.gov/Courts/SupremeCourt/_layouts/15/inplview.aspx"
        )

    def _process_html(self) -> None:
        """Extract content from JSON response

        :return: None
        """
        self.fetch_json()
        for row in self.request["response"].json()["Row"]:
            first_docket = row["FileLeafRef"][:-4].split(",")[0]
            name = row["Title"].split(first_docket)[0].strip("Nos. ")
            self.cases.append(
                {
                    "date": row["Published_x0020_Date"],
                    "docket": row["FileLeafRef"][:-4],
                    "name": name.strip(","),
                    "summary": row.get("Description0", ""),
                    "url": f"https://www.courts.ri.gov{row['FileRef']}",
                }
            )

    def build_url(self) -> str:
        """Generate URL for R.I. Supreme Court

        # This court hears things from mid-September to end of June. This
        # defines the "term" for that year, which triggers the website updates.

        :return: URL to call before scraping JSON endpoint
        """
        today = datetime.today()
        this_year = today.year
        term_end = datetime(this_year, 9, 15)
        year = this_year if today >= term_end else this_year - 1
        return f"https://www.courts.ri.gov/Courts/SupremeCourt/Supreme{self.opinion_type}/Forms/{year}{year+1}.aspx"
