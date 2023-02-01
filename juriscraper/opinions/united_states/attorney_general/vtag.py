"""
Scraper for Vermont Attorney General
CourtID: vtag
Court Short Name: Vermont AG
Author: William E. Palin
History:
 - 2023-01-29: Created.
"""
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.status = "Published"
        self.url = f"https://ago.vermont.gov/about-attorney-generals-office/attorney-general-opinions"

    def _process_html(self):
        """Process html

        :return: None
        """
        for row in self.html.xpath(".//article/div/div/ul/li/a/@href/../.."):
            url = row.xpath(".//a/@href")[0]
            if ".pdf" in url:
                year = row.text_content().split()[0]
                self.cases.append(
                    {
                        "url": url,
                        "docket": "",
                        "name": url.split("/")[-1][-4:],
                        "date": year,
                        "date_filed_is_approximate": True,
                        "summary": "",
                    }
                )
            else:
                self.url = url.replace(
                    "ago.vcms9.vt.prod.cdc.nicusa.com", "ago.vermont.gov"
                )
                self.html = super()._download()
                for row in self.html.xpath(".//article"):
                    links = row.xpath(".//a/@href")
                    for row in row.text_content().strip().split("#20")[1:]:
                        url = links.pop(0)
                        (
                            docket,
                            _,
                            _,
                            dated,
                            summary,
                            *_,
                        ) = f"#20{row}".strip().split("\n")
                        self.cases.append(
                            {
                                "name": docket,
                                "docket": docket,
                                "summary": summary,
                                "date": dated.split(":")[1].strip(),
                                "url": url,
                            }
                        )
