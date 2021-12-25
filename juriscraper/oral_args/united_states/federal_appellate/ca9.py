"""Scraper for Ninth Circuit of Appeals
CourtID: ca9
Court Short Name: ca9
"""

from juriscraper.OralArgumentSiteLinear import OralArgumentSiteLinear


class Site(OralArgumentSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "https://www.ca9.uscourts.gov/media/"

    def _download(self, request_dict={}):
        return super()._download(request_dict)

    def _process_html(self):
        path = "//table[@id='search-results-table']//tr"
        rows = self.html.xpath(path)
        for row in rows[1:-2]:
            parts = row.xpath(".//td[6]/a/@href")[0].split("/")
            year = parts[-3][1:5]
            month = parts[-3][5:7]
            day = parts[-3][7:]
            url = f"https://cdn.ca9.uscourts.gov/datastore/media/{year}/{month}/{day}/{parts[-2]}.mp3"
            self.cases.append(
                {
                    "date": row.xpath(".//td[5]/text()")[0],
                    "docket": row.xpath(".//td[2]/text()")[0],
                    "judge": row.xpath(".//td[3]/text()")[0],
                    "name": row.xpath(".//td[1]/text()")[0],
                    "url": url,
                }
            )
