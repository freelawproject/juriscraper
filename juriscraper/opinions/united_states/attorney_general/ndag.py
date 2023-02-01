"""
Scraper for North Dakota Attorney General
CourtID: ndag
Court Short Name: North Dakota AG
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
        self.url = "https://attorneygeneral.nd.gov/attorney-generals-office/legal-opinions/opinion-search"

    def _process_html(self):
        """Process html

        :return: None
        """
        for row in self.html.xpath(
            ".//tr/td/a[contains(@href, '.pdf')]/../.."
        ):
            cells = row.xpath(".//td")
            name = cells[1].text_content().strip()
            url = cells[1].xpath(".//a/@href")[0]
            self.cases.append(
                {
                    "url": url,
                    "docket": url.split("/")[-1][:-4],
                    "name": f"In Re: {name}",
                    "date": cells[0].text_content().strip(),
                }
            )
