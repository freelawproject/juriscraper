"""
Author: William Palin
Date created: 2023-01-21
Scraper for the Decisiones del Tribunal Apelaciones
CourtID: prapp
Court Short Name: Puerto Rico Court of Apelaciones
"""
from datetime import datetime

from dateparser import parse

from juriscraper.lib.string_utils import titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.status = "Published"

    def _old_download(self, request_dict={}):
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

    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        list_of_pr_months = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre','Diciembre']
        for year in range(start_date.year, end_date.year+1):
            for month in list_of_pr_months:
                try:
                    self.url = f"https://poderjudicial.pr/tribunal-apelaciones/decisiones-finales-del-tribunal-de-apelaciones/decisiones-del-tribunal-de-apelaciones-{month}-{year}/"
                    self.parse()
                    self.downloader_executed=False
                except Exception as e:
                    if str(e).__contains__('404 Client Error: Not Found for url'):
                        break
        return 0
