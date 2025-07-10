# Scraper for Superior Court of the Virgin Islands (published)
# CourtID: visuper_p

# History:
#   2023-12-11: Created - Garza
#   2024-01-15: Updated - Rossi
#   2025-07-09: Fixed - luism


from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = (
            "https://superior.vicourts.org/court_opinions/published_opinions"
        )
        self.status = "Published"
        self.should_have_results = True

    def _process_html(self) -> None:
        """Parse HTML into case objects

        :return: None
        """
        row_xpath = ".//table[@id='rfp-table']//tbody//tr[.//a[text() and not(@title='Summary')]]"
        for row in self.html.xpath(row_xpath):
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
                    "date": date_filed,
                    "docket": docket_number,
                    "name": case_name,
                    "url": url,
                    "judge": judge,
                    "citation": citation,
                }
            )
