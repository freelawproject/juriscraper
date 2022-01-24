"""Scraper for Dept of Justice Board of Immigration Appeals
CourtID: bia
Court Short Name: Dept of Justice Board of Immigration Appeals
Author: William Palin
Reviewer:
Type:
History:
    2021-12-18: Created by William E. Palin
"""
import re
from datetime import datetime
from typing import Any, Dict

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "https://www.justice.gov/eoir/ag-bia-decisions"
        self.article = None
        self.volume = 0
        self.urls = None

    def _process_elements(self, elements) -> Dict[str, Any]:
        """Process the element grouping.

        There is no easy way to parse our the content. Unfortunately, the DOJ
        admins randomly nest elements and not others. The only consistency
        is that they content is always split between HR tags.  So we iterate
        over the elements in order until we find an HR tag and then process
        the content.  Rinse Wash Repeat.

        Additionally, the only date we have is the year of the decision.

        :param elements: The elements between <hr> tags.
        :return: Case data
        """
        case = {}
        bold_text = elements[0].xpath(".//strong[1]/.. | .//b[1]/..")
        if not bold_text:
            return {}
        intro_text = (
            elements[0].xpath(".//strong[1]/.. | .//b[1]/..")[0].text_content()
        )
        intro_text = intro_text.replace(";", ",")
        name, cite = intro_text.split(",", 1)
        # Unfortunately there are no accessible file dates without PDF parsing
        # So we generate a date and mark it as date_filed_is_approximate = True
        # This is unset to false after it is extracted from the PDF on CL side.
        case["date_filed_is_approximate"] = True
        years = re.findall(r"\d{4}", cite)
        if not years:
            return {}
        case["date"] = f"{years[-1]}-07-01"
        case["status"] = "Published"
        case["citation"] = cite
        case["name"] = name
        case["url"] = elements[0].xpath(".//a")[0].get("href")
        case["docket"] = elements[0].xpath(".//a")[0].text_content()

        # Iterate over the P tags that hold the summaries, sometimes
        summary = []
        for element in elements:
            if element.tag == "p":
                summary.append(element.text_content())
        case["summary"] = "\n".join(summary).strip()
        return case

    def _process_html(self):
        if not self.test_mode_enabled():
            # Sort the URLS by volume to enable the backscraper
            # We reverse sort the links by volume and choose the first one
            # unless we are in a backscraper and then we choose what loop
            # we are in.
            if not self.urls:
                urls = self.html.xpath(
                    ".//table[1]/tbody/tr/td/a[contains(., 'Volume')]"
                )

                def get_text(elem):
                    return elem.text_content()

                self.urls = sorted(urls, key=get_text, reverse=True)
            self.url = self.urls[self.volume].get("href")
            # Download the new page of decisions
            self.html = super()._download()

        # Get the article which will contain all of our content.
        article = self.html.xpath(".//article")[0]
        # get the last element in the article
        # this ends the process_elements method on the final call because no
        # hr tag is present on the last decision

        last = list(article.iter())[-1]
        # Iterate over every tag in the article to separate out the cases.
        elements = []
        for element in article.iter():
            elements.append(element)
            # Process the data when the HR tag is found or the last element.
            # this loop lets us generate all of the elements and thus all
            # the data that we are looking for.  The DOJ has random and weird
            # HTML that sometimes nests and sometimes doesnt nest elements of
            # an opinion.
            if element.tag == "hr" or element == last:
                case = self._process_elements(elements)
                if case:
                    self.cases.append(case)
                elements, case = [], {}

    def extract_from_text(self, scraped_text: str) -> Dict[str, Any]:
        """Can we extract the date filed from the text?

        :param scraped_text: The content of the document downloaded
        :return: Metadata to be added to the case
        """
        date = re.findall(
            r"Decided (by (Acting\s)?Attorney General )?(.*\d{4})",
            scraped_text,
        )[0][-1]
        date_filed = datetime.strptime(date, "%B %d, %Y").strftime("%Y-%m-%d")
        metadata = {
            "OpinionCluster": {
                "date_filed": date_filed,
                "date_filed_is_approximate": False,
            },
        }
        return metadata
