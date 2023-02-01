"""
Scraper for Nebraska Attorney General
CourtID: nebag
Court Short Name: Nebraska AG
Author: William E. Palin
History:
 - 2023-01-29: Created.
"""

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.status = "Published"
        self.url = "https://ago.nebraska.gov/Opinions"

    def _process_html(self):
        """Process html

        :return: None
        """
        for row in self.html.xpath(".//tr/td/.."):
            cells = row.xpath(".//td")
            docket = cells[0].text_content()
            date = cells[1].text_content()
            name = cells[2].text_content()
            url = cells[3].xpath("//a/@href")[0]
            self.cases.append(
                {"url": url, "docket": docket, "name": name, "date": date}
            )
