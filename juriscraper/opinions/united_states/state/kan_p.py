# Scraper for Kansas Supreme Court
# CourtID: kan_p


from juriscraper.lib.html_utils import get_row_column_text
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.pages_to_process = 5
        self.court = "Supreme Court"
        self.status = "Published"
        self.url = "https://www.kscourts.org/Cases-Opinions/Opinions.aspx"

    def _set_parameters(self, page: int, viewstate: str) -> None:
        """Set Parameters for Kansas Courts

        :param page: Page number to request
        :param viewstate: Viewstate value
        :return: None
        """
        self.method = "POST"
        self.parameters = {
            "__EVENTARGUMENT": str(page),
            "__EVENTTARGET": "p$lt$zonePagePlaceholder$pageplaceholder$p$lt$ctl06$UniversalPager$pagerElem",
            "p$lt$zonePagePlaceholder$pageplaceholder$p$lt$ctl02$OpinionFilter1$filterControl$drpPublished": "Published",
            "p$lt$zonePagePlaceholder$pageplaceholder$p$lt$ctl02$OpinionFilter1$filterControl$drpCourt": self.court,
            "p$lt$zonePagePlaceholder$pageplaceholder$p$lt$ctl02$OpinionFilter1$filterControl$drpSortBy": "Opinion Date",
            "__VIEWSTATE": viewstate,
        }

    def _process_html(self):
        if self.test_mode_enabled():
            self.pages_to_process = 1

        for page in range(1, self.pages_to_process + 1):
            if not self.test_mode_enabled():
                viewstate = self.html.xpath("//input[@id='__VIEWSTATE']")[
                    0
                ].get("value")
                self._set_parameters(page, viewstate)
                self.html = self._download()

            rows = self.html.xpath("//table[@class='info-table']/tbody/div/tr")
            for row in rows[1:]:
                self.cases.append(
                    {
                        "date": row.xpath(f".//td[1]")[0].text_content(),
                        "docket": get_row_column_text(row, 2),
                        "name": get_row_column_text(row, 3),
                        "url": row.xpath(".//a[@class='link-pdf']")[0].get(
                            "href"
                        ),
                    }
                )
