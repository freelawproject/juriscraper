"""
Scraper for the Tennessee Court of Appeals
CourtID: tennctapp
Court Short Name: Tenn. Ct. App.
"""
from datetime import datetime

from juriscraper.opinions.united_states.state import tenn


class Site(tenn.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__

    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        start_date = start_date.date().strftime('%y-%m-%d')
        end_date = end_date.date().strftime('%y-%m-%d')
        page = 0
        flag = True
        while flag:
            self.url = f"https://www.tncourts.gov/views/ajax?_wrapper_format=drupal_ajax&view_name=opinions_apache_solr&view_display_id=block_1&view_args=28&view_path=%2Fnode%2F7163678&view_base_path=opinions&view_dom_id=2c5e5d1e2ea805ceb9c484bf11796085101a549951b41d790a274cb6ecb2f3d3&pager_element=0&viewsreference%5Bcompressed%5D=eJxdj0sKwzAMBe-idRb9EHBzGaNg1RXYrrHVlBBy98oYGshCSLx5s9AGDgVh2gCL_0RKAhPcDOwDUMI5kLOVRDj5eir9zwGEJZBGfauasSixOiyrlTU3qiH6gvkF5wI7xeYxHuDJFJxNGJs4Z7swfQ9aaOHK79TF-2iuyrrCQtE6Cu2ny_4D2BZNfw&viewsreference%5Bcompressed%5D=eJxdj0sKwzAMBe-idRb9EHBzGaNg1RXYrrHVlBBy98oYGshCSLx5s9AGDgVh2gCL_0RKAhPcDOwDUMI5kLOVRDj5eir9zwGEJZBGfauasSixOiyrlTU3qiH6gvkF5wI7xeYxHuDJFJxNGJs4Z7swfQ9aaOHK79TF-2iuyrrCQtE6Cu2ny_4D2BZNfw&field_opinions_county=All&field_opinions_authoring_judge=&field_opinions_originating_judge=&field_opinions_date_filed={start_date}&field_opinions_date_filed_1={end_date}&field_opinions_case_number=&title=&search_api_fulltext=&sort_by=field_opinions_date_filed&sort_order=DESC&page={page}&_drupal_ajax=1&ajax_page_state%5Btheme%5D=tncourts&ajax_page_state%5Btheme_token%5D=&ajax_page_state%5Blibraries%5D=eJx1j9FSxCAMRX8I4ZOYFGJLTQmSsHb9-o262q6jL3A59wwEEEGNpa6YlHtIIv51lPQSn8uO4uCxXr_bVe7ChKrYI-6NBbNBsqOEDIrNRMv_KTNW7EBuYlbRDi00bnzBfiLKTFraQWKDDrOFRcIPfDqgS0BYM9hP7sHrghu6mXkmjFCBrlqSPf8LuNPNuY8G5A_iR21joiILZidXUdzCBIJOcdfYUco7hlP2X5vTmqKNiLCVOlsCHRL-gp7K9GHz6GqzEU9AVl3JFHcp-Cbhc_Wwwv4ANs6D8Ab-uLWZ"
            self.parse()
            pageination = self.html.xpath(
                "//ul[@class='pagination js-pager__items']//li/a/span/text()")
            if 'Next page' in pageination:
                page = page + 1
            else:
                flag = False
            self.downloader_executed = False
        return 0

    def get_court_name(self):
        return "Tennessee Court of Appeals"

    def get_class_name(self):
        return 'tennctapp'
