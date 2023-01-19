"""Scraper for the Air Force Court of Criminal Appeals
CourtID: afcca
Court Short Name: Air Force Court of Criminal Appeals
Reviewer: mlr
History:
    15 Sep 2014: Created by Jon Andersen
"""

from datetime import date

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url_base = "http://afcca.law.af.mil/content/opinions_date_%d.html"
        self.url = self.url_base % date.today().year
        self.disable_certificate_verification()

    def _process_html(self):
        for row in self.html.xpath(".//img[contains(@src, 'pdf.gif')]/../..")[
            :-1
        ]:
            status = row.xpath(".//td")[3].text_content()
            if status != "Published":
                status = "Unpublished"
            self.cases.append(
                {
                    "url": row.xpath(".//td/a/@href")[0],
                    "docket": row.xpath(".//td")[2].text_content(),
                    "name": row.xpath(".//td/a")[0].text_content(),
                    "date": row.xpath(".//td")[4].text_content(),
                    "status": status,
                }
            )
