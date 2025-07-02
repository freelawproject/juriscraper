"""
Scraper for Kansas Supreme Court
CourtID: kan
Court Short Name: Kansas
Author: William Palin
Court Contact:
History:
 - 2025-06-09: Created.
Notes: This is a selenium scraper and must start or redirect from somewhere else
"""

import re

from lxml.html import fromstring

from juriscraper.OpinionSiteLinearWebDriven import OpinionSiteLinearWebDriven


class Site(OpinionSiteLinearWebDriven):
    link_xp = '//div[@class="col-md-6"][1]/ul/li'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "https://free.law"
        self.uses_selenium = True
        self.should_have_results = True

    def _process_html(self):
        """Process with selenium

        :return: None
        """
        if not self.test_mode_enabled():
            self.initiate_webdriven_session()
            self.url = "https://searchdro.kscourts.gov/Data/decisionsList"
            self.webdriver.get(self.url)
            self.html = fromstring(self.webdriver.page_source)
        else:
            with open(self.url) as f:
                self.html = fromstring(f.read())

        links = self.html.xpath(self.link_xp)
        for link in links:
            # Get previous date
            date_string = link.xpath("preceding::h5[1]/text()")[0].strip()
            row_string = link.text_content().strip()
            row_text = re.sub(r"\s+", " ", row_string)
            docket, name = row_text.split(" - ")
            name, status = name.split("(")

            url = link.xpath(".//a/@href")[0]
            self.cases.append(
                {
                    "docket": docket,
                    "name": name,
                    "status": status[:-1],
                    "date": date_string,
                    "url": f"https://searchdro.kscourts.gov{url}",
                }
            )

        if not self.test_mode_enabled():
            self.close_webdriver_session()
