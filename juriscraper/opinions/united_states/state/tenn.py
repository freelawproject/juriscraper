"""
Scraper for the Supreme Court of Tennessee
CourtID: tenn
Court Short Name: Tenn.
"""
from datetime import datetime

from typing_extensions import override

from juriscraper.OpinionSiteLinear import OpinionSiteLinear
from juriscraper.lib.html_utils import fix_links_in_lxml_tree


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.status = "Published"

    def _process_html(self):
        # print(self.html)
        self.html = self.html[2]['data']
        text = self._clean_text(self.html)
        html_tree = self._make_html_tree(text)
        if hasattr(html_tree, "rewrite_links"):
            html_tree.rewrite_links(fix_links_in_lxml_tree,
                                    base_href=self.request["url"])
        self.html = html_tree
        for row in self.html.xpath("//tr"):
            date = (row.xpath(
                ".//td[contains(@class, 'views-field-field-opinions-date-filed')]")[
                        0].text_content().strip())
            lower_court = (row.xpath(
                ".//td[contains(@class, 'views-field-field-opinions-county')]")[
                               0].text_content().strip())
            section = row.xpath(
                ".//td[contains(@class, 'views-field-field-opinions-case-number')]")[
                0]
            url = section.xpath(".//a")[0].get("href")
            name = section.xpath(".//a")[0].text_content()
            rows = [row.strip() for row in
                    section.text_content().strip().split("\n", 4)]
            judge = rows[2]
            if judge is not None and str(judge).__contains__(":"):
                judge = [judge.split(": ")[1]]
            else:
                judge = []
            self.cases.append(
                {"date": date, "lower_court": lower_court, "url": url,
                 "name": name, "docket": [rows[1]], "judge": judge,
                 "summary": rows[-1], })

    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        start_date = start_date.date().strftime('%y-%m-%d')
        end_date = end_date.date().strftime('%y-%m-%d')
        page = 0
        flag = True
        while flag:
            self.url = f"https://www.tncourts.gov/views/ajax?_wrapper_format=drupal_ajax&view_name=opinions_apache_solr&view_display_id=block_1&view_args=27&view_path=%2Fnode%2F7163679&view_base_path=opinions&view_dom_id=d6ce5aca4e1c2a6072082eb32e6628c871ad260ba2d444aa1e4aa562bf99698d&pager_element=0&viewsreference%5Bcompressed%5D=eJxdj9EKgzAMRf8lzz7Ixjbnz5RIsy7QdqXNHCL-uymFCT6EhHvuecgKFgVhXAGz-waKAiNcHrB1QBEnT9YUEuHoyqn0PzsQFk8ata1qwqzE6LAsRpZUqYboMqY3nAtsFQ_P-wFeTN6aiKGKUzIz0--gmWYu_IlNvN6GXllTWCgYS77-1G8714hNfg&viewsreference%5Bcompressed%5D=eJxdj9EKgzAMRf8lzz7Ixjbnz5RIsy7QdqXNHCL-uymFCT6EhHvuecgKFgVhXAGz-waKAiNcHrB1QBEnT9YUEuHoyqn0PzsQFk8ata1qwqzE6LAsRpZUqYboMqY3nAtsFQ_P-wFeTN6aiKGKUzIz0--gmWYu_IlNvN6GXllTWCgYS77-1G8714hNfg&field_opinions_county=All&field_opinions_authoring_judge=&field_opinions_originating_judge=&field_opinions_date_filed={start_date}&field_opinions_date_filed_1={end_date}&field_opinions_case_number=&title=&search_api_fulltext=&sort_by=field_opinions_date_filed&sort_order=DESC&page={page}&_drupal_ajax=1&ajax_page_state%5Btheme%5D=tncourts&ajax_page_state%5Btheme_token%5D=&ajax_page_state%5Blibraries%5D=eJx1j9FSxCAMRX8I4ZOYFGJLTQmSsHb9-o262q6jL3A59wwEEEGNpa6YlHtIIv51lPQSn8uO4uCxXr_bVe7ChKrYI-6NBbNBsqOEDIrNRMv_KTNW7EBuYlbRDi00bnzBfiLKTFraQWKDDrOFRcIPfDqgS0BYM9hP7sHrghu6mXkmjFCBrlqSPf8LuNPNuY8G5A_iR21joiILZidXUdzCBIJOcdfYUco7hlP2X5vTmqKNiLCVOlsCHRL-gp7K9GHz6GqzEU9AVl3JFHcp-Cbhc_Wwwv4ANs6D8Ab-uLWZ"
            self.parse()
            pageination = self.html.xpath(
                "//ul[@class='pagination js-pager__items']//li/a/span/text()")
            if 'Next page' in pageination:
                page = page + 1
            else:
                flag = False
            self.downloader_executed = False
        return 0

    def get_state_name(self):
        return "Tennessee"

    def get_court_type(self):
        return 'state'

    def get_court_name(self):
        return "Supreme Court of Tennessee"

    def get_class_name(self):
        return 'tenn'
