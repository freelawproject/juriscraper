# Scraper for Supreme Court of Oklahoma
# CourtID: okla
# Court Short Name: OK
# Court Contact: webmaster@oscn.net
# Author: Andrei Chelaru
# Reviewer: mlr
# Date: 2014-07-05


from lxml import html

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "https://www.oscn.net/decisions/ok/30"
        self.status = "Published"
        self.expected_content_types = ["text/html"]

    def _process_html(self):
        for row in self.html.xpath(".//li[@class='decision']"):
            name, citation = row.xpath(".//a/text()")
            url = row.xpath(".//a/@href")[0]
            date_filed_raw = row.xpath(".//span[@class='decidedDate']/text()")[
                0
            ].strip()
            docket_number_raw = row.xpath(
                ".//span[@class='caseNumber']/text()"
            )[0].strip()
            summary = row.xpath(".//p[@class='summaryParagraph']/text()")[0]

            self.cases.append(
                {
                    "date": date_filed_raw.split()[1],
                    "name": name,
                    "docket": docket_number_raw.split()[1],
                    "citation": citation,
                    "url": url,
                    "summary": summary.strip(),
                }
            )

    @staticmethod
    def cleanup_content(content):
        tree = html.fromstring(content)
        core_element = tree.xpath("//*[@id='oscn-content']")[0]
        return html.tostring(
            core_element, pretty_print=True, encoding="unicode"
        ).encode("utf-8")
