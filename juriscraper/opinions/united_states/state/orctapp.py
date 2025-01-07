"""
Scraper for Oregon Court of Appeals
CourtID: orctapp
Court Short Name: OR Ct App
Author: William Palin
History:
    - 2023-11-18: Created
"""
from datetime import datetime

from lxml import html

from juriscraper.DeferringList import DeferringList
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = (
            "https://www.courts.oregon.gov/publications/coa/Pages/default.aspx"
        )
        # https://cdm17027.contentdm.oclc.org/digital/search/advanced
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
            ul_elements = header.xpath("./following-sibling::ul[position()<=2]")
            for ul in ul_elements:
                for item in ul.xpath(".//li"):
                    anchors = item.xpath(".//a")
                    if not (len(anchors) > 1):
                        continue

                    text = item.text_content().strip()
                    print(f"text : {text}")
                    url = anchors[0].xpath("./@href")[0]
                    print(f"url : {url}")
                    docket = anchors[1].text_content().strip()
                    print(f"docket : {docket}")
                    name = text.split(")", 1)[-1].strip()
                    citation = text.split("(",1)[0].strip()
                    print (f"name : {name}")
                    print(f"citation : {citation}")

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

    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        if not self.downloader_executed:
            self.html = self._download()
            # print(html.tostring(self.html,pretty_print=True).decode('UTF-8'))
            self._process_html()

        for attr in self._all_attrs:
            self.__setattr__(attr, getattr(self, f"_get_{attr}")())

        self._clean_attributes()
        if "case_name_shorts" in self._all_attrs:
            self.case_name_shorts = self._get_case_name_shorts()
        self._post_parse()
        self._check_sanity()
        self._date_sort()
        self._make_hash()
        return len(self.cases)

    def get_court_name(self):
        return "Supreme Court of Oregon"

    def get_court_type(self):
        return "state"

    def get_class_name(self):
        return "orctapp"

    def get_state_name(self):
        return "Oregon"
