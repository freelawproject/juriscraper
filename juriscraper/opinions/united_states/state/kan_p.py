#  Scraper for Kansas Supreme Court
# CourtID: kan_p

import lxml.html

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.pages_to_process = 5
        self.court = "Supreme Court"
        self.status = "Published"
        self.url = "https://www.kscourts.org/Cases-Opinions/Opinions.aspx"
        slug = "p$lt$zonePagePlaceholder$pageplaceholder$p$lt$ctl02$OpinionFilter1$filterControl"
        self.parameters = {
            f"{slug}$drpPublished": self.status,
            f"{slug}$drpCourt": self.court,
            f"{slug}$drpSortBy": "Opinion Date",
        }

    def _process_html(self) -> None:
        vs = self.html.xpath("//input[@id='__VIEWSTATE']")[0].get("value")
        self.parameters["__VIEWSTATE"] = vs
        for page in range(1, self.pages_to_process + 1):
            self.parameters["__EVENTARGUMENT"] = page
            self._request_url_post(self.url)
            rows = self.html.xpath("//table[@class='info-table']/tbody/div/tr")
            for row in rows[1:]:
                self.cases.append(
                    {
                        "date": row.xpath(f".//td[1]")[0].text_content(),
                        "docket": self.get_cell_text(row, 2),
                        "name": self.get_cell_text(row, 3),
                        "url": row.xpath(".//a[@class='link-pdf']")[0].get(
                            "href"
                        ),
                    }
                )

    def get_cell_text(self, row: lxml.html.Element, index: int) -> str:
        """Return the text of cell [index] in row"""
        return row.xpath(f".//td[{index}]")[0].text_content().strip()
