"""Scraper for the Texas Attorney General
CourtID: texag
Court Short Name: Texas Attorney General
History:
    2017-02-04: Created by Ardery
    2018-10-13: Retired by Ardery
    2023-01-28: Updated by William E. Palin
"""

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "https://texasattorneygeneral.gov/opinions"

    def _process_html(self):
        cases = self.html.xpath("//div[@class='sidebar-ag-opinion-content']")
        for case in cases:
            docket = case.xpath(".//h4")[0].text_content().strip()
            summary = case.xpath(".//p")[0].text_content().strip()
            url = case.xpath(".//h4/a/@href")[0]
            name = f"Untitled Texas Attorney General Opinion: {docket}"
            date = case.xpath(
                ".//div[@class='sidebar-ag-opinion-casedate']/text()"
            )[0].strip()
            self.cases.append(
                {
                    "name": name,
                    "docket": docket,
                    "date": date,
                    "url": url,
                    "summary": summary,
                    "status": "Published",
                }
            )
