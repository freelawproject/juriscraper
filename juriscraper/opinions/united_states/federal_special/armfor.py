"""Scraper for the United States Court of Appeals for the Armed Forces
CourtID: armfor
Court Short Name: C.A.A.F."""

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.back_scrape_iterable = [""]
        self.url = (
            "https://www.armfor.uscourts.gov/newcaaf/opinions/CurrentOpins.htm"
        )
        self.row_base_path = (
            ".//td/font/a[contains(@href, '.pdf')]/ancestor::tr"
        )
        self.status = "Published"

    def _process_html(self):
        for row in self.html.xpath(self.row_base_path):
            case_name, docket, date, cite = row.xpath(".//td")
            cite = "" if "xx" in cite.text_content() else cite.text_content()
            self.cases.append(
                {
                    "name": case_name.text_content(),
                    "url": docket.xpath(".//a/@href")[0],
                    "date": date.text_content().strip(),
                    "citation": cite,
                    "docket": docket.text_content().split()[0],
                }
            )
