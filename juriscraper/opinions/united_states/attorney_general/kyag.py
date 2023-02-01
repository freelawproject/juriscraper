"""
Scraper for Kentucky Attorney General
CourtID: kentuckyag
Court Short Name: Kentucky AG
Author: William E. Palin
History:
 - 2023-01-29: Created.
"""
import json

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.status = "Published"
        self.url = (
            f"https://www.ag.ky.gov/Resources/Opinions/Pages/Opinions.aspx"
        )

    def _download(self, request_dict={}):
        """Process tricky html

        :param request_dict: Empty parameters
        :return: HTML
        """
        if self.test_mode_enabled():
            with open(self.url) as f:
                self.json = json.load(f)
            return
        if not self.html:
            return super()._download()
        else:
            keys = [
                x.get("data-key")
                for x in self.html.xpath(".//input[@type='checkbox']")
            ]
            self.parameters = {
                "SiteUrl": "https://www.ag.ky.gov/Resources/Opinions",
                "ListsToCount": "|9328041e-55d9-4eee-a2f2-818633a986a6",
                "ListId": "9328041e-55d9-4eee-a2f2-818633a986a6",
                "Lookup": f"431acfbd-683c-4cfb-8eed-ec00b33dbdf7:{keys[0]},|",
                "SearchText": "",
                "PageId": "0",
                "PageSize": "50",
                "ShowNoResultMessage": "True",
                "OperatorType": "AND",
                "SortField": "",
                "SortDirection": "Ascending",
                "SortValue": "",
                "Sort": "Year New:Descending|Title:Descending|",
                "ItemTemplateFields": "URL;Date;Title;Subject;",
                "_": "1675110975546",
            }
            self.headers = {
                "Host": "www.ag.ky.gov",
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.2 Safari/605.1.15",
            }
            self.url = "https://www.ag.ky.gov/_layouts/15/Fwk.Webparts.Agency.Ui/Search/Search.ashx"
            self.json = (
                self.request["session"]
                .get(
                    url=self.url, params=self.parameters, headers=self.headers
                )
                .json()
            )

    def _process_html(self):
        """Process the html

        :return: None
        """
        self._download()
        for item in self.json["Items"]:
            name, date, summary = None, None, None
            for field in item["Fields"]:
                if field["Name"] == "Title":
                    name = field["Value"]
                elif field["Name"] == "Date":
                    date = field["Value"]
                elif field["Name"] == "Subject":
                    summary = field["Value"]

            self.cases.append(
                {
                    "url": item["Url"],
                    "name": name,
                    "docket": name,
                    "date": date,
                    "summary": summary,
                }
            )
