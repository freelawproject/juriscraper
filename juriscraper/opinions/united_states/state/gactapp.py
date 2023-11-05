# Scraper for Georgia Appeals Court
# CourtID: gactapp
# Court Short Name: gactapp
# Author: Andrei Chelaru
# Reviewer: mlr
# Date created: 25 July 2014


from datetime import date, timedelta

from juriscraper.lib.string_utils import titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        today = date.today().strftime("%Y-%m-%d")
        last_week = (date.today() - timedelta(days=7)).strftime("%Y-%m-%d")
        self.status = "Published"
        self.url = f"https://www.gaappeals.us/wp-content/themes/benjamin/docket/docketdate/results_all.php?OPstartDate={last_week}&OPendDate={today}&submit=Start+Opinions+Search"

    def _process_html(self):
        for row in self.html.xpath("//tr")[::-1][:-1]:
            docket, name, date, disposition, _, url = row.xpath(".//td")
            self.cases.append(
                {
                    "docket": docket.text_content(),
                    "name": titlecase(name.text_content()),
                    "date": date.text_content(),
                    "disposition": disposition.text_content().title(),
                    "url": url.xpath(".//a")[0].get("href"),
                }
            )
