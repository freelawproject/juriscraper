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
"""

import re
from datetime import date, datetime
from urllib.parse import urljoin

from lxml import etree, html

from juriscraper.lib.date_utils import unique_year_month
from juriscraper.lib.html_utils import strip_bad_html_tags_insecure
from juriscraper.lib.string_utils import titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    court_name = "Supreme Judicial Court"
    first_opinion_date = datetime(2017, 6, 20)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "https://www.socialaw.com/customapi/slips/getopinions"
        self.court_id = self.__module__
        self.search_date = datetime.today()
        self.parameters = {
            "SectionName": self.court_name,
            "ArchiveDate": self.search_date.strftime("%B %Y"),
        }
        self.method = "POST"
        self.status = "Published"
        self.expected_content_types = ["text/html"]
        self.should_have_results = True
        self.days_interval = 30
        self.make_backscrape_iterable(kwargs)

    def _process_html(self):
        """Scrape and process the JSON endpoint

        :return: None
        """
        for row in self.html:
            url = urljoin(
                "https://www.socialaw.com/services/slip-opinions/",
                row["UrlName"],
            )
            details = row["Details"]
            caption = titlecase(row.get("Parties"))
            caption = re.sub(r"(\[\d{1,2}\])", "", caption)

            judge_str = details.get("Present", "")
            judge_str = re.sub(r"(\[\d{1,2}\])", "", judge_str)
            judge_str = re.sub(r"\, JJ\.", "", judge_str)
            judge_str = re.sub(
                r"(Associate\s+)?Justice*|of the Superior Court", "", judge_str
            )

            # Clear judge_str if it matches a date like 'July 16, 2024'
            if re.match(r"^[A-Za-z]+\s+\d{1,2},\s+\d{4}$", judge_str.strip()):
                judge_str = ""

            self.cases.append(
                {
                    "name": caption,
                    "judge": judge_str,
                    "date": row["Date"],
                    "url": url,
                    "docket": details["Docket"],
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
        self.search_date = search_date
        self.parameters = {
            "SectionName": self.court_name,
            "ArchiveDate": self.search_date.strftime("%B %Y"),
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
