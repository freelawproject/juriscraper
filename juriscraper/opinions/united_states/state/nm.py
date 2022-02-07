import datetime
import re
from typing import Any, Dict

from juriscraper.lib.string_utils import titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    """This court's website is implemented by Decisia, a software
    that has built-in anti-bot detection. If you make too many
    requests in rapid succession, the site will render a captcha
    page instead of rendering the real page content. Since the
    docket numbers for unpublished opinions are not published on
    the main results page (but on sub-info pages), we may (likely)
    need to issues multiple sub-requests for each crawl to retrieve
    the docket info for unpublished opinions.

    Given the above, we need to track and limit the number of
    sub-requests we make in order to prevent triggering the
    anti-bot detection, which would trigger the captcha and
    crash our scraping.

    If we ever wanted to implement a back scraper for this court,
    we'd likely need to create a separate class to handle it. In order
    to do this, we'd need to use the 'Advanced Search' mechanism to
    find all results. The results page will render 25 results. But,
    in a browser, when you scroll down, more results populate dynamically
    on the page via javascript.  So, we'd need to hit the page via a
    phantomjs webdriver and keep loading results. To make things more
    complicated, we'd also need to batch our (sub) requests in order
    to prevent triggering the anti-bot detection. I've testing sleeping
    for 1 minute every 40 requests, and that seems to work. Consequently,
    the back scraper would take a very very long time to run, but if we
    needed to do it, it can probably be done with the above method.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.year = datetime.date.today().year
        self.url = f"https://nmonesource.com/nmos/nmsc/en/{self.year}/nav_date.do?iframe=true"
        self.rate_limit = "100/5m"
        self.rate_group = "nm"
        self.request_count = 0

    def _process_html(self):
        self.request_count += 1
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
            metadata = row.xpath(".//span[@class='subMetadata']/text()")
            if cite:
                citation = cite[0].text_content().strip()
            else:
                citation = ""
            if metadata:
                status = (
                    "Published" if "Reported" in metadata else "Unpublished"
                )
            else:
                status = "Unpublished"
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
