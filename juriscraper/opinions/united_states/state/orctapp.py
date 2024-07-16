"""
Scraper for Oregon Court of Appeals
CourtID: orctapp
Court Short Name: OR Ct App
Author: William Palin
History:
    - 2023-11-18: Created
"""

from juriscraper.DeferringList import DeferringList
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = (
            "https://www.courts.oregon.gov/publications/coa/Pages/default.aspx"
        )
        self.cases = []
        self.status = "Published"
        self.court_code = "p17027coll5"

    def fetch_url_json(self, identifier):
        """"""
        url = f"https://ojd.contentdm.oclc.org/digital/bl/dmwebservices/index.php?q=dmQuery/{self.court_code}/identi^{identifier}^all^and/title!subjec!descri!dmrecord/title/1024/1/0/0/0/0/json"
        json = self.request["session"].get(url).json()
        return f"https://ojd.contentdm.oclc.org/digital/api/collection/{self.court_code}/id/{json['records'][0]['pointer']}/download"

    def _process_html(self):
        for header in self.html.xpath("//h4//a/parent::h4"):
            date_string = header.text_content().strip()
            if not date_string:
                continue
            ul = header.xpath("./following-sibling::ul")[0]
            for item in ul.xpath(".//li"):
                # Ensure two links are present (skip Petitions for Review rows)
                # see or_example_2.html
                anchors = item.xpath(".//a")
                if not (len(anchors) > 1):
                    continue
                text = item.text_content().strip()
                url = anchors[0].xpath("./@href")[0]
                docket = anchors[1].text_content().strip()
                name = text.split(")", 1)[-1]
                self.cases.append(
                    {
                        "date": date_string,
                        "name": name,
                        "docket": docket,
                        "url": url,
                    }
                )

    def _get_download_urls(self):
        """Get download urls

        :return: List URLs
        """

        def fetcher(case):
            if self.test_mode_enabled():
                return case["url"]

            return self.fetch_url_json(case["url"].split("=")[-1][:-4])

        return DeferringList(seed=self.cases, fetcher=fetcher)
