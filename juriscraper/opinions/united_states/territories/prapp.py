"""
Author: William Palin
Date created: 2023-01-21
Scraper for the Decisiones del Tribunal Supremo
CourtID: prapp
Court Short Name: Puerto Rico
"""

from datetime import date

from juriscraper.lib.string_utils import titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        year = date.today().year
        self.url = f"https://poderjudicial.pr/tribunal-apelaciones/decisiones-finales-del-tribunal-de-apelaciones/"
        self.status = "Published"

    def _download(self, request_dict={}):
        if self.test_mode_enabled():
            return super()._download()
        if not self.html:
            self.html = super()._download()
        self.url = self.html.xpath(
            ".//ul[1]/li/a[contains(@href, 'decisiones-finales-del-tribunal-de-apelaciones/decisiones-del-tribunal-de-apelaciones')]/../.."
        )[0].xpath(".//a/@href")[-1]
        return super()._download()

    def _process_html(self):
        for row in self.html.xpath(".//table/tbody/tr"):
            cells = row.xpath(".//td")
            maybe_link = cells[0].xpath(".//a/@href")
            if not maybe_link:
                continue
            else:
                url = maybe_link[0]

            self.cases.append(
                {
                    "name": titlecase(cells[1].text_content()),
                    "url": url,
                    "docket": cells[0].text_content(),
                    "date": cells[2].text_content(),
                }
            )
