"""Scraper for Army Court of Criminal Appeals
CourtID: acca
Reviewer: None
History:
  2015-01-08: Created by mlr
  2016-03-17: Website appears to be dead. Scraper disabled in __init__.py.
  2019-09-11: Rewritten by arderyp to user Linear pattern
"""

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "https://www.jagcnet.army.mil/ACCALibrary/cases/opinions/OC"
        self.status = "Published"
        self.expected_content_types = ["application/octet-stream"]

    def _process_html(self):
        for row in self.html.xpath(
            '//*[@id="Opinions_ResizeContainer"]/table/tbody/tr'
        ):
            col1, col2, col3 = row.xpath(".//td")
            url = col1.xpath(".//a/@href")
            if not url:
                continue
            name = col1.text_content()
            docket = col2.text_content()
            date = col3.text_content()
            self.cases.append(
                {
                    "date": date.strip(),
                    "docket": docket.strip(),
                    "name": name.strip(),
                    "url": url[0],
                }
            )
