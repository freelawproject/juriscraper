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
        self.url = "https://www.jagcnet.army.mil/85257546006DF36B/ODD?OpenView&Count=-1"
        self.status = "Published"

    def _process_html(self):
        for row in self.html.xpath('//tr[@class="domino-viewentry"]'):
            cell_three = row.xpath(".//td[3]")[0]
            text = cell_three.text_content()
            text_parts = text.split("-", 1)
            hrefs = cell_three.xpath(".//a/@href")

            # skip rows without link to opinion
            if not hrefs:
                continue

            self.cases.append(
                {
                    "date": row.xpath(".//td[1]")[0].text_content(),
                    "docket": text_parts[0],
                    "name": text_parts[1],
                    "url": hrefs[0],
                }
            )
