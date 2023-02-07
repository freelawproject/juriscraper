"""
Author: William Palin
Date created: 2023-01-21
Scraper for the Decisiones del Tribunal Apelaciones
CourtID: prapp
Court Short Name: Puerto Rico Court of Apelaciones
"""
from dateparser import parse

from juriscraper.lib.string_utils import titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = f"https://poderjudicial.pr/tribunal-apelaciones/decisiones-finales-del-tribunal-de-apelaciones/"
        self.status = "Published"

    def _download(self, request_dict={}):
        """Download websites

        :param request_dict: Empty dict
        :return: HTML object
        """
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
            date_obj = parse(cells[2].text_content(), languages=["es"])

            self.cases.append(
                {
                    "name": titlecase(cells[1].text_content()),
                    "url": url,
                    "docket": cells[0].text_content(),
                    "date": str(date_obj.date()),
                }
            )
