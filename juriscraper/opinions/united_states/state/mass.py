"""
Scraper for Massachusetts Supreme Court
CourtID: mass
Court Short Name: MS
Author: Andrei Chelaru
Court Contact: SJCReporter@sjc.state.ma.us (617) 557-1030
Reviewer: mlr
History:
 - 2014-07-12: Created.
 - 2014-08-05, mlr: Updated regex.
 - 2014-09-18, mlr: Updated regex.
 - 2016-09-19, arderyp: Updated regex.
 - 2017-11-29, arderyp: Moved from RSS source to HTML
    parsing due to website redesign
 - 2023-01-28, William Palin: Updated scraper
 - 2025-12-18, Luis Manzur: Updated scraper
"""

import re
from datetime import date, datetime

from dateutil.relativedelta import relativedelta
from lxml import etree, html

from juriscraper.AbstractSite import logger
from juriscraper.lib.date_utils import unique_year_month
from juriscraper.lib.html_utils import strip_bad_html_tags_insecure
from juriscraper.lib.string_utils import titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    court_name = "Supreme Judicial Court"
    first_opinion_date = datetime.now() - relativedelta(
        months=3
    )  # the site only have last 3 month available

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "https://www.socialaw.com/services/slip-opinions/"
        self.request["parameters"]["params"] = {
            "Court": self.court_name,
        }
        self.court_id = self.__module__
        self.status = "Published"
        self.expected_content_types = ["text/html"]
        self.days_interval = 30
        self.make_backscrape_iterable(kwargs)

    def _process_html(self):
        """Scrape and process the JSON endpoint

        :return: None
        """
        rows = self.html.xpath(
            "//div[@id='slip-opinion-list-accordion']//div[@class='accordion-item']"
        )

        for row in rows:
            name = row.xpath(".//strong[@class='title sh2']")[0].text.strip()

            # clean name participants enum
            name = titlecase(re.sub(r"\[\d\]", "", name))

            date = row.xpath(".//span[@class='date sh3']")[0].text.strip()
            docket = row.xpath(
                ".//div[@class='section-header']/div[@class='rich-text rich-text-sm']"
            )[0].text.strip()
            url = row.xpath(".//a")[0].get("href")

            self.cases.append(
                {
                    "name": name,
                    "date": date,
                    "docket": docket,
                    "url": url,
                }
            )

    @staticmethod
    def cleanup_content(content):
        """Remove non-opinion HTML

        Cleanup HMTL from Social Law page so we can properly display the content

        :param content: The scraped HTML
        :return: Cleaner HTML
        """
        content = content.decode("utf-8")
        tree = strip_bad_html_tags_insecure(content, remove_scripts=True)
        content = tree.xpath(
            "//div[@id='contentPlaceholder_ctl00_ctl00_ctl00_detailContainer']"
        )[0]
        new_tree = etree.Element("html")
        body = etree.SubElement(new_tree, "body")
        body.append(content)
        return html.tostring(new_tree).decode("utf-8")

    def _download_backwards(self, search_date: date) -> None:
        """Download and process HTML for a given target date.

        :param search_date (date): The date for which to download and process opinions.
        :return None; sets the target date, downloads the corresponding HTML
        and processes the HTML to extract case details.
        """

        logger.info("Backscraping for %s", search_date.strftime("%B %Y"))
        self.request["parameters"]["params"] = {
            "Court": self.court_name,
            "Month": search_date.strftime("%B %Y"),
        }
        self.html = self._download()
        self._process_html()

    def make_backscrape_iterable(self, kwargs) -> None:
        """Make back scrape iterable

        :param kwargs: the back scraping params
        :return: None
        """

        super().make_backscrape_iterable(kwargs)
        self.back_scrape_iterable = unique_year_month(
            self.back_scrape_iterable
        )
