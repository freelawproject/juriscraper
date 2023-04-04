import datetime
import re
from typing import Any, Dict

from juriscraper.lib.string_utils import titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    """This site has an artificial limit of 50/1 minute and 100/5 minutes.

    To stay under that cap we are going to just request the first 10 opinions.  Judging on the number of opinions
    filed in each court we should be fine.

    Additionally, we moved docket number capture to PDF extraction, to limit the number of requests.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.year = datetime.date.today().year
        self.url = f"https://nmonesource.com/nmos/nmsc/en/{self.year}/nav_date.do?iframe=true"

    def _process_html(self):
        rows = self.html.xpath(
            ".//li[contains(./@class, 'list-item-expanded')]"
        )
        for row in rows:
            url = row.xpath(
                ".//a[contains(@title, 'Download the PDF version')]/@href"
            )[0]
            name = (
                row.xpath(".//span[@class='title']")[0].text_content().strip()
            )
            date = (
                row.xpath(".//span[@class='publicationDate']")[0]
                .text_content()
                .strip()
            )
            cite = row.xpath(".//span[@class='citation']")
            metadata = row.xpath(".//div[@class='subMetadata']/span/text()")
            if cite:
                citation = cite[0].text_content().strip()
            else:
                citation = ""
            if metadata:
                status = (
                    "Published"
                    if "Reported" in metadata[-1]
                    else "Unpublished"
                )
            else:
                status = "Unpublished"

            if len(self.cases) >= 10:
                # Limit to max of 10 cases per crawl to stay under limit.
                continue

            self.cases.append(
                {
                    "date": date,
                    "docket": "",
                    "name": titlecase(name),
                    "citation": citation,
                    "url": url,
                    "status": status,
                }
            )

    def extract_from_text(self, scraped_text: str) -> Dict[str, Any]:
        """Pass scraped text into function and return data as a dictionary

        :param scraped_text: Text of scraped content
        :return: metadata
        """
        docket_number = re.findall(r"N[oO]\.\s(.*)", scraped_text)[0]
        metadata = {
            "OpinionCluster": {
                "docket_number": docket_number,
            },
        }
        return metadata
