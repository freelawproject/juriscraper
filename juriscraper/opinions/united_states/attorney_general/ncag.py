"""
Scraper for North Carolina Attorney General
CourtID: ncag
Court Short Name: North Carolina AG
Author: William E. Palin
History:
 - 2023-01-29: Created.
"""

from lxml.html import fromstring, tostring

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.status = "Published"
        self.url = (
            f"https://ncdoj.gov/legal-services/legal-opinions-directory/"
        )

    def _process_html(self):
        """Process html

        :return: None
        """
        for row in self.html.xpath(".//tr/td/a/../.."):
            url = row.xpath(".//td/a/@href")[0]
            name = row.xpath(".//td/a/text()")[0]
            date = row.xpath(".//td")[0].text_content()
            self.cases.append(
                {
                    "url": url,
                    "docket": "",
                    "name": name,
                    "date": date,
                }
            )

    @staticmethod
    def cleanup_content(content):
        """Process the HTML into content because PDF doesnt exist

        :param content:
        :return:
        """
        tree = fromstring(content)
        core_element = tree.xpath(".//main")[0]
        return (core_element.text or "") + "".join(
            [
                tostring(child, pretty_print=True, encoding="unicode")
                for child in core_element.iterchildren()
            ]
        )
