from datetime import date, timedelta

from juriscraper.lib.html_utils import get_table_column_text
from juriscraper.lib.string_utils import convert_date_string
from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        begin_date = date.strftime(date.today() - timedelta(15), "%m/%d/%Y")
        end_date = date.strftime(date.today(), "%m/%d/%Y")
        self.url = (
            "http://wicourts.gov/supreme/scopin.jsp?"
            "begin_date=%s&end_date=%s&SortBy=date"
        ) % (begin_date, end_date)
        self.court_id = self.__module__
        self.table_id = "scopinion"
        self.path_base = f"//table[@id='{self.table_id}']"

    def _get_case_names(self):
        return get_table_column_text(self.html, 3, False, self.table_id)

    def _get_download_urls(self):
        path = f"{self.path_base}//td[4]//a[contains(., 'PDF')]/@href"
        return self.html.xpath(path)

    def _get_case_dates(self):
        path = f"{self.path_base}//td[1]"
        cells = self.html.xpath(path)
        return [convert_date_string(cell.text_content()) for cell in cells]

    def _get_docket_numbers(self):
        return get_table_column_text(self.html, 2, False, self.table_id)

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_names)
