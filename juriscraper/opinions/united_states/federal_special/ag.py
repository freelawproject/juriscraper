"""Scraper for the United States Department of Justice Attorney General
CourtID: ag
Court Short Name: United States Attorney General
"""

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "https://www.justice.gov/olc/opinions?items_per_page=40"
        self.status = "Published"

    def _process_html(self):
        for row in self.html.xpath(".//article"):
            name = row.xpath(".//h2")[0].text_content().strip()
            url = row.xpath(".//a/@href")[0]
            date = row.xpath(".//time")[0].text_content()
            if not name:
                continue
            summary = row.xpath(".//p")[0].text_content()
            self.cases.append(
                {
                    "date": date,
                    "name": name,
                    "url": url,
                    "summary": summary,
                    "docket": "",  # Docket numbers don't appear to exist.
                }
            )
