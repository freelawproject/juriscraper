# Scraper for Superior Court of the Virgin Islands (published)
# CourtID: visuper_p

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = (
            "https://superior.vicourts.org/court_opinions/published_opinions"
        )
        self.request["verify"] = False
        self.status = "Published"
        self.court = "Superior Court"

    def _process_html(self):
        for row in self.html.xpath(".//tbody//tr"):
            (
                case_name,
                date_filed,
                docket_number,
                judge,
                citation,
                _summary,
            ) = row.xpath(".//td//text()")
            url = row.xpath(".//td/a")[0].get("href")
            self.cases.append(
                {
                    "status": self.status,
                    "date": date_filed,
                    "docket": docket_number,
                    "name": case_name,
                    "url": url,
                    "judge": judge,
                    "citation": citation,
                }
            )
