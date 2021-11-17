"""
Scraper for the United States Bankruptcy Appellate Panel for the Ninth Circuit
CourtID: bap9
Court Short Name: 9th Cir. BAP
"""

from juriscraper.lib.string_utils import titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "http://www.ca9.uscourts.gov/bap/"
        self.court_id = self.__module__
        self.method = "POST"
        self.parameters = {
            "c_mode": "view",
            "c_page_size": "500",
        }

    def _process_html(self):
        path = "//table[@id='search-results-table']//tr[position()>1]"
        for row in self.html.xpath(path):
            cell_1 = row.xpath("./td[1]")[0]
            url = cell_1.xpath(".//a/@href")
            if not url:
                continue
            type = row.xpath("./td[2]")[0].text_content()
            if "Unpublished" in type:
                status = "Unpublished"
            elif "Published" in type:
                status = "Published"
            else:
                status = "Unknown"
            self.cases.append(
                {
                    "url": url[0],
                    "name": f"In re: {titlecase(cell_1.text_content())}",
                    "status": status,
                    "docket": row.xpath("./td[3]")[0].text_content(),
                    "date": row.xpath("./td[4]")[0].text_content(),
                }
            )
