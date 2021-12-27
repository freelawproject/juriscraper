"""
Scraper for Court of Appeals of Arizona, Division 2
CourtID: arizctapp_div_2
Court Short Name: arizctapp_div_2
Author: Andrei Chelaru
Reviewer: mlr
History:
    2014-07-23: Created by Andrei Chelaru
    2021-12-10: URL changed to recent opinions page, satsuki-chan
"""

from juriscraper.lib.string_utils import clean_if_py3, titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        # Feeling down and tired of of your regular life? Check out this website.
        self.url = "https://www.appeals2.az.gov/ODSPlus/recentOpinionsHTML.cfm"
        self.cases = []

    def _process_html(self) -> None:
        path = "//table//a[contains(@href, '.pdf')]"
        for item in self.html.xpath(path):
            docket = item.xpath("./text()")[0]
            url = item.xpath("./@href")[0]
            name = item.xpath("./following::td[1]/*/text()")[0]
            # Expected: "Opinion Filed: 10/13/2021"
            date_string = item.xpath("./following::td[2]/text()")[0].strip()
            date = clean_if_py3(date_string).rsplit(":", 1)[1].strip()
            summary_list = item.xpath("./following::tr[1]//text()")
            summary = "".join(summary_list).strip()
            self.cases.append(
                {
                    "name": titlecase(name),
                    "date": date,
                    "docket": docket,
                    "url": url,
                    "summary": summary,
                    "status": "Published",
                }
            )
