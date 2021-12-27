"""Scraper for Missouri
CourtID: mo
Court Short Name: MO
Author: Ben Cassedy
Date created: 04/27/2014
"""

from datetime import date

from juriscraper.lib.string_utils import convert_date_string
from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url_slug = "Supreme"
        self.url = self.build_url()
        self.cases = []

    def build_url(self):
        url_template = "https://www.courts.mo.gov/page.jsp?id=12086&dist=Opinions %s&date=all&year=%s#all"
        return url_template % (self.url_slug, date.today().year)

    def _download(self, request_dict={}):
        html = super()._download(request_dict)
        self._extract_cases_from_html(html)
        return html

    def _extract_cases_from_html(self, html):
        for date_block in html.xpath(
            "//div[@id='content']/div/form/table/tr/td"
        ):
            date_string = date_block.xpath("input/@value")
            if date_string:
                for case_block in date_block.xpath("table/tr/td"):
                    links = case_block.xpath("a")
                    first_link_text = links[0].xpath("text()")
                    if (
                        first_link_text
                        and "Orders Pursuant to Rules" in first_link_text[0]
                    ):
                        continue

                    target_link_index = 1 if len(links) > 1 else 0
                    bolded_text = case_block.xpath("b")
                    docket = self.sanitize_docket(
                        bolded_text[0].xpath("text()")[0]
                    )
                    text = case_block.xpath("text()")
                    (
                        judge,
                        disposition,
                    ) = self.parse_judge_disposition_from_text(text)

                    self.cases.append(
                        {
                            "date": convert_date_string(date_string[0]),
                            "docket": docket,
                            "judge": judge,
                            "url": links[target_link_index].xpath("@href")[0],
                            "name": links[target_link_index].xpath("text()")[
                                0
                            ],
                            "disposition": disposition,
                        }
                    )

    @staticmethod
    def sanitize_docket(docket):
        for substring in [":", "and", "_", "Consolidated", "(", ")", ","]:
            docket = docket.replace(substring, " ")
        return ", ".join(docket.split())

    @staticmethod
    def parse_judge_disposition_from_text(text_raw_list):
        text_clean_list = [
            text.strip() for text in text_raw_list if text.strip()
        ]
        return text_clean_list[0], text_clean_list[1]

    def _get_download_urls(self):
        return [case["url"] for case in self.cases]

    def _get_case_names(self):
        return [case["name"] for case in self.cases]

    def _get_case_dates(self):
        return [case["date"] for case in self.cases]

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.cases)

    def _get_docket_numbers(self):
        return [case["docket"] for case in self.cases]

    def _get_judges(self):
        return [case["judge"] for case in self.cases]

    def _get_dispositions(self):
        return [case["disposition"] for case in self.cases]
