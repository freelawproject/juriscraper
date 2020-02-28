# Scraper for New York Appellate Divisions 1st Dept.
# CourtID: nyappdiv_1st
# Court Short Name: NY
# Author: Andrei Chelaru
# Reviewer: mlr
# Date: 2014-07-04

from datetime import date
from dateutil.rrule import rrule, MONTHLY

from juriscraper.AbstractSite import logger
from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.html_utils import get_html5_parsed_text
from juriscraper.lib.string_utils import convert_date_string


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        date_keys = rrule(
            MONTHLY, dtstart=date(2003, 11, 1), until=date(2015, 8, 30)
        )
        self.back_scrape_iterable = [i.date() for i in date_keys]
        self.row_base_path = '//tr[contains(./td[1]/a/@href, "3d")]'
        self.division = 1
        self.url = self.build_url()

    def _get_case_names(self):
        path = "%s/td[1]" % self.row_base_path
        return [cell.text_content() for cell in self.html.xpath(path)]

    def build_url(self, target_date=False):
        base = (
            "http://www.courts.state.ny.us/reporter/slipidx/aidxtable_%s"
            % self.division
        )
        if target_date:
            return "%s_%s_%s.shtml" % (
                base,
                target_date.year,
                target_date.strftime("%B"),
            )
        else:
            return "%s.shtml" % base

    def _get_download_urls(self):
        path = "%s/td[1]//a/@href" % self.row_base_path
        return self.html.xpath(path)

    def _get_case_dates(self):
        case_dates = []
        for element in self.html.xpath("//caption | //center"):
            date_string = (
                element.text_content().strip().replace("Cases Decided ", "")
            )
            path_prefix = (
                "./parent::"
                if element.tag == "caption"
                else "./following-sibling::"
            )
            path = path_prefix + "table[1]" + self.row_base_path
            cases = element.xpath(path)
            case_dates.extend([convert_date_string(date_string)] * len(cases))
        return case_dates

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_names)

    def _get_docket_numbers(self):
        path = "%s/td[3]" % self.row_base_path
        return map(
            self._add_str_to_list_where_empty_element, self.html.xpath(path)
        )

    def _get_judges(self):
        path = "%s/td[2]" % self.row_base_path
        return map(
            self._add_str_to_list_where_empty_element, self.html.xpath(path)
        )

    def _get_neutral_citations(self):
        path = "%s/td[4]" % self.row_base_path
        return [cell.text_content().strip() for cell in self.html.xpath(path)]

    @staticmethod
    def _add_str_to_list_where_empty_element(element):
        string_list = element.xpath("./text()")
        return string_list[0] if string_list else ""

    def _download_backwards(self, target_date):
        self.crawl_date = target_date
        logger.info("Running backscraper with date: %s" % target_date)
        self.url = self.build_url(target_date=target_date)
        self.html = self._download()

    def _make_html_tree(self, text):
        return get_html5_parsed_text(text)
