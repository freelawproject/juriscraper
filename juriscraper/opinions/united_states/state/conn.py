# coding=utf-8
"""Scraper for Connecticut Supreme Court
CourtID: conn
Court Short Name: Conn.
Author: Asadullah Baig <asadullahbeg@outlook.com>

History:
 - 2014-07-11: created
 - 2014-08-08, mlr: updated to fix InsanityError on case_dates
 - 2014-09-18, mlr: updated XPath to fix InsanityError on docket_numbers
 - 2015-06-17, mlr: made it more lenient about date formatting
 - 2016-07-21, arderyp: fixed to handle altered site format
 - 2017-01-10, arderyp: restructured to handle new format use case that includes
        opinions without dates and flagged for 'future' publication
"""

from lxml import etree
from datetime import date

from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.string_utils import convert_date_string, normalize_dashes


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.crawl_date = date.today()
        self.url = "http://www.jud.ct.gov/external/supapp/archiveAROsup{year}.htm".format(
            year=self.crawl_date.strftime("%y")
        )
        self.court_id = self.__module__
        self.cases = []

    def _download(self, request_dict={}):
        html = super(Site, self)._download(request_dict)
        self._extract_cases_from_html(html)
        return html

    def _extract_cases_from_html(self, html):
        """Build list of data dictionaries, one dictionary per case (table row)."""
        # Strip inconsistently placed <font> and <br>
        # tags that make stable coverage almost impossible
        etree.strip_tags(html, "font", "br")
        path = '//table[@id="AutoNumber1"]//ul'
        for ul in html.xpath(path):
            preceding = ul.xpath("./preceding::*[1]")[0]
            preceding_text = " ".join(preceding.text_content().split()).strip(
                ":"
            )
            # Skip sections that are marked to be published at future date
            if preceding_text and not preceding_text.lower().endswith(" date"):
                # Below will fail if they change up string format
                date_string = preceding_text.split()[-1]
                case_date = convert_date_string(date_string)
                for element in ul.xpath("./li | ./a"):
                    if element.tag == "li":
                        text = normalize_dashes(
                            " ".join(element.text_content().split())
                        )
                        if not text:
                            continue
                        anchor = element.xpath(".//a")[0]
                    elif element.tag == "a":
                        # Malformed html, see connappct_example.html
                        anchor = element
                        glued = "%s %s" % (anchor.text_content(), anchor.tail)
                        text = normalize_dashes(" ".join(glued.split()))
                    self.cases.append(
                        {
                            "date": case_date,
                            "url": anchor.xpath("./@href")[0],
                            "docket": text.split("-")[0]
                            .replace("Concurrence", "")
                            .replace("Dissent", ""),
                            "name": text.split("-", 1)[1],
                        }
                    )

    def _get_case_names(self):
        return [case["name"] for case in self.cases]

    def _get_download_urls(self):
        return [case["url"] for case in self.cases]

    def _get_case_dates(self):
        return [case["date"] for case in self.cases]

    def _get_docket_numbers(self):
        return [case["docket"] for case in self.cases]

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.cases)
