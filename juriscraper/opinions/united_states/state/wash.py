from datetime import datetime

import requests
from juriscraper.OpinionSiteLinear import OpinionSiteLinear
from sample_caller import logger


class Site(OpinionSiteLinear):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.year = datetime.today().year
        self.url = f"https://www.courts.wa.gov/opinions/index.cfm?fa=opinions.byYear&fileYear={self.year}&crtLevel=S&pubStatus=PUB"
        self.status = "Published"

        self._opt_attrs = self._opt_attrs + ["case_info_url","case_info_html"]

        self.valid_keys.update({
            "case_info_url",
            "case_info_html"
        })
        self._all_attrs = self._req_attrs + self._opt_attrs

        # Set all metadata to None
        for attr in self._all_attrs:
            self.__setattr__(attr, None)

    def _get_case_info_url(self):
        return self._get_optional_field_by_id("case_info_url")

    def _get_case_info_html(self):
        print("in case_info_html")
        return self._get_optional_field_by_id("case_info_html")

    def _process_html(self):
        self.request["headers"].update(
            {
                "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Connection":"keep-alive",
                "Cookie":"multiFileOk=Yes; CFID=Z2ogdxrz2onkq05aeo41pi9s2csi1nbj1iipd7lp9md6ozsuece-9341949; CFTOKEN=Z2ogdxrz2onkq05aeo41pi9s2csi1nbj1iipd7lp9md6ozsuece-628d4dd593eefe47-407C0827-DB9D-D6D7-166C93B75C5F893D; multiFileOk=Yes; TS017905d7=0129531cb0f8cc7c4e60672afc6ccd314bfb0805d47469f06f6c1f3fa92337bc63ad2d10010e0ebfd3b9fce693bdd57149924905d3",
                "User-Agent":"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:132.0) Gecko/20100101 Firefox/132.0"
            }
        )
        for row in self.html.xpath('//tr/td[@valign="top"]/..')[::-1]:
            if len(row.xpath(".//td")) != 4:
                continue
            date, middle, name, op_type = row.xpath(".//td")
            info_url = middle.xpath("a")[0].get("href")
            try:
                response = requests.get(info_url,
                                        headers=self.request["headers"],
                                        proxies=self.proxies,timeout=120)
                print(response.status_code)
                if response.status_code == 200:
                    case_info_html = response.text  # Print the response content
                else:
                    case_info_html = ""
            except Exception as e:
                logger.info(f"error while downloading case info {e}")
                case_info_html=""

            self.cases.append(
                {
                    "date": date.text_content(),
                    "url": middle.xpath("a")[1].get("href"),
                    "name": name.text_content().replace("* ", ""),
                    "docket": [middle.xpath("a")[0].text_content()],
                    "case_info_url": middle.xpath("a")[0].get("href"),
                    "case_info_html":case_info_html
                }
            )

    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:

        if not self.downloader_executed:
            self.html = self._download()
            # print(html.tostring(self.html, pretty_print=True).decode('utf-8'))
            self._process_html()

        for attr in self._all_attrs:
            self.__setattr__(attr, getattr(self, f"_get_{attr}")())

        self._clean_attributes()
        if "case_name_shorts" in self._all_attrs:
            self.case_name_shorts = self._get_case_name_shorts()
        self._post_parse()
        self._check_sanity()
        self._date_sort()

        return len(self.cases)

    def get_court_name(self):
        return "Supreme Court of Washington"

    def get_state_name(self):
        return "Washington"

    def get_class_name(self):
        return "wash"

    def get_court_type(self):
        return "state"
