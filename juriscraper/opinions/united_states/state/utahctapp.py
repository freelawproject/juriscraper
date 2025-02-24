import re
from datetime import datetime
from urllib.parse import quote

from juriscraper.OpinionSiteLinear import OpinionSiteLinear
from juriscraper.opinions.united_states.state import utah

class Site(utah.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "https://www.utcourts.gov/opinions/appopin/index.php"
        self.court_id = self.__module__
        self.regex = r"Case No. (.*?), Filed (.*?), (\d{4} UT App \d+)"

    # def _process_html(self) -> None:
    #     for row in self.html.xpath("//a[@class='pdf']/parent::p"):
    #         link = row.xpath("./a")[0]
    #         x = " ".join(row.xpath(".//text()")).strip()
    #         if "Superseded" in x:
    #             continue
    #         m = re.search(self.regex, x)
    #         if not m:
    #             continue
    #         date = m.groups()[1]
    #         if "Filed" in date:
    #             date = date.replace("Filed", "").strip()
    #         citation = m.groups()[2]
    #         docket_number = m.groups()[0].strip().split(",")
    #
    #         self.cases.append(
    #             {
    #                 "date": date,
    #                 "name": row.xpath(".//text()")[0],
    #                 "citation": [citation],
    #                 "url": quote(link.attrib["href"], safe=":/"),
    #                 "docket": docket_number,
    #                 "status": "Published",
    #             }
    #         )
    #
    # def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
    #     if not self.downloader_executed:
    #         self.html = self._download()
    #         self._process_html()
    #
    #     for attr in self._all_attrs:
    #         self.__setattr__(attr, getattr(self, f"_get_{attr}")())
    #
    #     self._clean_attributes()
    #     if "case_name_shorts" in self._all_attrs:
    #         self.case_name_shorts = self._get_case_name_shorts()
    #     self._post_parse()
    #     self._check_sanity()
    #     self._date_sort()
    #     self._make_hash()
    #     return len(self.cases)

    # def get_court_type(self):
    #     return "state"

    def get_class_name(self):
        return "utahctapp"

    # def get_state_name(self):
    #     return "Utah"

    def get_court_name(self):
        return "Utah Court of Appeals"
