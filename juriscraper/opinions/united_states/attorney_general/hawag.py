"""
Scraper for Hawaii Attorney General
CourtID: hawag
Court Short Name: Hawaii AG
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
        self.url = "https://ag.hawaii.gov/publications/ag-opinions/"

    def _process_html(self):
        """Process the html

        :return: None
        """
        for row in self.html.xpath(".//a[contains(@href, '.pdf')]/.."):
            date = row.text_content().split()[0].replace("/", "-")
            url = row.xpath(".//a/@href")[0]
            name = row.xpath(".//a")[0].text_content()
            docket = name.split(":")[0]
            if name == docket:
                docket = name.split("(")[-1][:-1].upper()
            self.cases.append(
                {"url": url, "docket": docket, "name": name, "date": date}
            )
