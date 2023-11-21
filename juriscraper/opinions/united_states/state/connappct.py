"""Scraper for Connecticut Appellate Court
CourtID: connctapp
Court Short Name: Connappct.
Author: Asadullah Baig<asadullahbeg@outlook.com>
Date created: 2014-07-11
History:
    - 2022-02-02, satsuki-chan: Updated to Opinionsitelinear
    - 2023-11-20, William Palin: Updated
"""

from datetime import date

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.year = date.today().strftime("%y")
        self.url = f"http://www.jud.ct.gov/external/supapp/archiveAROap{self.year}.htm"
        self.status = "Published"

    def _process_html(self) -> None:
        """Process the html and extract out the opinions

        :return: None
        """
        for date_section in self.html.xpath("//ul"):
            b = date_section[0].xpath(".//preceding::b[1]")[0]
            date = b.text_content().strip().split("of")[-1].strip()[:-1]
            for li in date_section.xpath(".//li"):
                link = li.xpath(".//a")[0]
                link_text = link.text_content()
                docket = link.text_content()
                name = li.text_content().replace(link_text, "").strip()
                self.cases.append(
                    {
                        "date": date,
                        "url": link.get("href"),
                        "docket": docket,
                        "name": name,
                    }
                )
