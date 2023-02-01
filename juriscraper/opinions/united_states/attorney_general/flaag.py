"""
Scraper for Florida Attorney General
CourtID: flaag
Court Short Name: Florida AG
Author: William E. Palin
History:
 - 2023-01-29: Created.
"""

from lxml import html

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.status = "Published"
        self.url = "http://myfloridalegal.com/ago.nsf/Opinions"
        self.seeds = []

    def _process_html(self):
        """Process the html

        :return: None
        """
        for row in self.html.xpath(
            ".//td/a[contains(@href, 'ago.nsf/Opinions')]/.."
        ):
            if (
                "INFORMAL" in row.text_content()
                or "AGO" not in row.text_content()
            ):
                continue
            docket = row.text_content()
            url = row.xpath(".//a/@href")[0]
            date = row.getnext().text_content()
            summary = row.getnext().text_content()
            self.cases.append(
                {
                    "url": url,
                    "docket": docket,
                    "name": f"Advisory Legal Opinion - {docket}",
                    "summary": summary,
                    "date": date,
                }
            )

    @staticmethod
    def cleanup_content(content) -> str:
        """Process the HTML into content because PDF doesnt exist

        :param content: Rough HTML content
        :return: Cleaned HTML content
        """
        tree = html.fromstring(content)
        core_elements = tree.xpath(".//div[@id='txt']")
        opinion = []
        for el in core_elements:
            content = (el.text or "") + "".join(
                [
                    html.tostring(child, pretty_print=True, encoding="unicode")
                    for child in el.iterchildren()
                ]
            )
            opinion.append(content)
        return "".join(opinion).split("</div>", 1)[1].strip()
