"""
Scraper for Oregon Attorney General
CourtID: orag
Court Short Name: Oregon AG
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
        self.url = "https://www.doj.state.or.us/oregon-department-of-justice/office-of-the-attorney-general/attorney-general-opinions/"

    def _process_html(self):
        """Process html

        :return: None
        """
        for row in self.html.xpath(".//div/div[@class='result-wrapper']"):
            docket = row.xpath(".//p")[0].text_content()
            name = f"Opinion Request {docket}"
            url = row.xpath(".//p/a/@href")[0]
            date = row.xpath(".//p")[1].text_content()
            self.cases.append(
                {
                    "url": url,
                    "docket": docket,
                    "name": name,
                    "date": date,
                }
            )
