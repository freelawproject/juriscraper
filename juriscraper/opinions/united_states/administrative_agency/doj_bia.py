"""Scraper for Dept of Justice. Board of Immigration Appeals
CourtID: doj_bia
Court Short Name: Dept of Justice. Board of Immigration Appeals
Author: William Palin
Reviewer:
Type:
History:
    2021-12-18: Created by William E. Palin
"""

import re

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "https://www.justice.gov/eoir/ag-bia-decisions"
        self.article = None

    def _download(self, request_dict={}):
        html = super()._download(request_dict)
        self.url = html.xpath(".//table//tbody/tr/td/a/@href")[0]
        return self._get_html_tree_by_url(self.url)

    def _process_html(self):
        tables = self.html.xpath(
            ".//table/following-sibling::p/preceding-sibling::table"
        )
        for table in tables:
            bold_text = table.xpath(".//strong | .//b")
            if not bold_text:
                continue
            bold_text = bold_text[0]
            cite = " ".join(
                bold_text.xpath(".//following-sibling::text()")
            ).strip(" ,")
            year = re.findall("\d{4}", cite)[0]
            docket = table.xpath(".//a")[0]
            name = bold_text.xpath(".//text()")[0]
            self.cases.append(
                {
                    "name": name,
                    "cite": cite,
                    "year": year,
                    "docket": docket.text_content(),
                    "url": docket.get("href"),
                    "status": "Unpublished",
                    "date": f"{year}-07-01",
                }
            )
