"""Scraper for Dept of Justice. Board of Immigration Appeals
CourtID: bia
Court Short Name: Dept of Justice. Board of Immigration Appeals
Author: William Palin
Reviewer:
Type:
History:
    2021-12-18: Created by William E. Palin
"""

from typing import Any, Dict

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
        if self.test_mode_enabled():
            return html
        return self._get_html_tree_by_url(self.url)

    def _process_elements(self, elements) -> Dict[str, Any]:
        """Process the element grouping.

        They extra nest and its a real pain to get everything.

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
        name, cite = intro_text.split(",", 1)
        # Unfortunately there are no accessible file dates without PDF parsing
        # So we generate a date and mark it as date_filed_is_approximate = True
        case["date_filed_is_approximate"] = True
        case["date"] = f"{cite[-5:-1]}-07-01"
        case["status"] = "Unpublished"
        case["neutral_citation"] = cite
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
        article = self.html.xpath(".//article")[0]
        # get the last element in the article, this triggers the process_elements
        # method on the final call.
        *_, last = article.iter()
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
