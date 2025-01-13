import re

from juriscraper.AbstractSite import logger
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "https://legacy.utcourts.gov/opinions/supopin/"
        self.court_id = self.__module__
        self.status = "Published"

    def _process_html(self):
        for row in self.html.xpath(
            "//div[@id='content']//p[a[contains(@href, '.pdf')]]"
        ):
            if row.xpath("br"):
                # Superseded opinions
                logger.info("Skipping row %s", row.text_content())
                continue

            # pick longest text; if not, HTML comments may cause wrong indexing
            text = sorted(row.xpath("text()"))[-1]
            neutral_cite_match = re.search(r"\d{4} UT( App)? \d{1,}", text)
            citation = neutral_cite_match.group(0)

            filed_index = text.find("Filed")
            docket = text[:filed_index].strip(", ")
            date_filed = text[
                filed_index + 5 : neutral_cite_match.start()
            ].strip(" ,")

            self.cases.append(
                {
                    "url": row.xpath("a")[0].get("href"),
                    "name": row.xpath("a")[0].text_content(),
                    "date": date_filed,
                    "citation": citation,
                    "docket": docket,
                }
            )
