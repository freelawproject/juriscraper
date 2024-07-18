"""
Court Contact: https://www.supremecourt.gov/contact/contact_webmaster.aspx
"""

from datetime import date

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    justices = {
        "A": "Samuel Alito",
        "AB": "Amy Coney Barrett",
        "AS": "Antonin Scalia",
        "B": "Stephen Breyer",
        "BK": "Brett Kavanaugh",
        "D": "Decree",
        "DS": "David Souter",
        "EK": "Elana Kagan",
        "G": "Ruth Bader Ginsburg",
        "JS": "John Paul Stephens",
        "K": "Anthony Kennedy",
        "KJ": "Ketanji Brown Jackson",
        "NG": "Neil Gorsuch",
        "PC": "Per Curiam",
        "R": "John G. Roberts",
        "SS": "Sonia Sotomayor",
        "T": "Clarence Thomas",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.yy = self._get_current_term()
        self.status = "Published"
        self.url_base = "https://www.supremecourt.gov/opinions"
        self.precedential = "Published"
        self.court = "slipopinion"
        self.url = f"{self.url_base}/{self.court}/{self.yy}"

    @staticmethod
    def _get_current_term():
        """The URLs for SCOTUS correspond to the term, not the calendar.

        The terms kick off on the first Monday of October, so we use October 1st
        as our cut off date.
        """
        today = date.today()
        term_cutoff = date(today.year, 10, 1)
        if today < term_cutoff:
            # Haven't hit the cutoff, return previous year.
            return int(today.strftime("%y")) - 1  # y3k bug!
        else:
            return today.strftime("%y")

    def _process_html(self):
        for row in self.html.xpath("//tr"):
            cells = row.xpath(".//td")
            if len(cells) != 6:
                continue
            a, date, docket, link, justice, citation = row.xpath(".//td")
            if not link.text_content():
                continue
            self.cases.append(
                {
                    "citation": citation.text_content(),
                    "date": date.text_content(),
                    "url": link.xpath(".//a/@href")[0],
                    "name": link.text_content(),
                    "docket": docket.text_content(),
                    "judge": self.justices[justice.text_content()],
                }
            )
