"""
Scraper for Pennsylvania Supreme Court
CourtID: pa
Court Short Name: pa
"""
import re

from juriscraper.lib.html_utils import get_xml_parsed_text
from juriscraper.lib.string_utils import convert_date_string
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.regex = False
        self.url = "https://www.pacourts.us/Rss/Opinions/Supreme/"
        self.set_regex(r"(.*)(?:[,-]?\s+Nos?\.)(.*)")
        self.base = (
            "//item[not(contains(title/text(), 'Judgment List'))]"
            "[not(contains(title/text(), 'Reargument Table'))]"
            "[not(contains(title/text(), 'Order Amending Rules'))]"
            "[contains(title/text(), 'No.')]"
        )
        self.cases = []

    def _make_html_tree(self, text):
        return get_xml_parsed_text(text)

    def _process_html(self):
        for item in self.html.xpath(self.base):
            judges = item.xpath(
                "./dc:creator/text()", namespaces=self.html.nsmap
            )
            pubdate = item.xpath("./pubDate/text()")[0]
            title = item.xpath("./title/text()")[0]
            search = self.regex.search(title)
            url = item.xpath("./atom:link/@href", namespaces=self.html.nsmap)[
                0
            ]
            if search:
                name = search.group(1)
                docket = search.group(2)
            else:
                name = title
                docket = ""
            self.cases.append(
                {
                    "name": name,
                    "date": convert_date_string(pubdate),
                    "docket": docket,
                    "judge": judges[0] if judges else "",
                    "url": url,
                }
            )

    def _get_case_names(self):
        return [case["name"] for case in self.cases]

    def _get_download_urls(self):
        return [case["url"] for case in self.cases]

    def _get_case_dates(self):
        return [case["date"] for case in self.cases]

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.cases)

    def _get_docket_numbers(self):
        return [case["docket"] for case in self.cases]

    def _get_judges(self):
        return [case["judge"] for case in self.cases]

    def set_regex(self, pattern):
        self.regex = re.compile(pattern)
