# Scraper for Oklahoma Attorney General Opinions
# CourtID: oklaag
# Court Short Name: OK
# Author: Andrei Chelaru
# Reviewer: mlr
# Date: 2014-07-05

from datetime import date

from lxml import html

from juriscraper.opinions.united_states.state import okla

## WARNING: THIS SCRAPER IS FAILING:
## This scraper is succeeding in development, but
## is failing in production.  We are not exactly
## sure why, and suspect that the hosting court
## site may be blocking our production IP and/or
## throttling/manipulating requests from production.


class Site(okla.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        year = date.today().year
        self.url = f"http://www.oscn.net/applications/oscn/Index.asp?ftdb=STOKAG&year={year}&level=1"
        self.court_id = self.__module__
        self.status = "Unpublished"

    def _process_html(self):
        for row in self.html.xpath("//div/p['@class=document']")[::-1]:
            if "OK" not in row.text_content():
                continue
            if "EMAIL" in row.text_content():
                continue
            citation, date, name = row.text_content().split(",", 2)
            self.cases.append(
                {
                    "date": date,
                    "name": name,
                    "docket": "",
                    "url": row.xpath(".//a")[0].get("href"),
                    "citation": citation,
                }
            )

    @staticmethod
    def cleanup_content(content):
        tree = html.fromstring(content)
        core_element = tree.xpath('//div[@id="oscn-content"]/div')[0]
        return html.tostring(
            core_element, pretty_print=True, encoding="unicode"
        ).encode("utf-8")
