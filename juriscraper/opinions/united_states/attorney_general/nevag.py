"""
Scraper for Nevada Attorney General
CourtID: nevag
Court Short Name: Nevada AG
Author: William E. Palin
History:
 - 2023-01-29: Created.--- could probably use a text extract for the date but
#  would you believe that the pdfs are images.
"""

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.status = "Published"
        self.url = "https://ag.nv.gov/Publications/Opinions/"

    def _process_html(self):
        """Process html

        :return: None
        """
        for row in self.html.xpath(".//a"):
            if "AGO-" not in row.text_content():
                continue
            name = row.text_content()
            docket = name
            url = row.xpath(".//@href")[0]
            self.cases.append(
                {
                    "url": url,
                    "docket": docket,
                    "name": name,
                    "date": name.split("-")[1],
                    "date_filed_is_approximate": True,
                }
            )
