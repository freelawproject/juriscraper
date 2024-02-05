# Scraper for Supreme Court of Oklahoma
# CourtID: okla
# Court Short Name: OK
# Court Contact: webmaster@oscn.net
# Author: Andrei Chelaru
# Reviewer: mlr
# Date: 2014-07-05


from datetime import datetime

from lxml import html

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        year = datetime.today().year
        self.url = f"https://www.oscn.net/applications/oscn/Index.asp?ftdb=STOKCSSC&year={year}&level=1"
        self.status = "Published"
        self.expected_content_types = ["text/html"]

    def _process_html(self):
        for row in self.html.xpath("//div/p['@class=document']")[::-1]:
            if "OK" not in row.text_content():
                continue
            if "EMAIL" in row.text_content():
                continue
            if "P.3d" in row.text_content():
                citation1, citation2, date, name = row.text_content().split(
                    ",", 3
                )
                citation = f"{citation1} {citation2}"
            else:
                citation, date, name = row.text_content().split(",", 2)

            self.cases.append(
                {
                    "date": date,
                    "name": name,
                    "docket": citation,
                    "url": row.xpath(".//a")[0].get("href"),
                    "citation": citation,
                }
            )

    @staticmethod
    def cleanup_content(content):
        tree = html.fromstring(content)
        core_element = tree.xpath("//*[@id='oscn-content']")[0]
        return html.tostring(
            core_element, pretty_print=True, encoding="unicode"
        ).encode("utf-8")
