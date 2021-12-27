"""
CourtID:	ca6
Court Contact:	WebSupport@ca6.uscourts.gov
"""

from juriscraper.lib.string_utils import clean_if_py3, convert_date_string
from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "http://www.opn.ca6.uscourts.gov/opinions/opinions.php"

    def _get_case_names(self):
        return [
            string.split(" - ")[0]
            for string in self.get_nth_table_cell_data(4)
        ]

    def _get_download_urls(self):
        return self.get_nth_table_cell_data(1, href=True)

    def _get_case_dates(self):
        return [
            convert_date_string(date)
            for date in self.get_nth_table_cell_data(3)
        ]

    def _get_docket_numbers(self):
        return self.get_nth_table_cell_data(2)

    def _get_precedential_statuses(self):
        statuses = []
        for file_name in self.get_nth_table_cell_data(1, link_text=True):
            if "n" in file_name.lower():
                statuses.append("Unpublished")
            elif "p" in file_name.lower():
                statuses.append("Published")
            else:
                statuses.append("Unknown")
        return statuses

    def get_nth_table_cell_data(self, n, href=False, link_text=False):
        path = "//table/tr/td[%d]" % n
        if href:
            path += "/a/@href"
        elif link_text:
            path += "/a/text()"
        else:
            path += "/text()"

        results = []
        for data in self.html.xpath(path):
            data = clean_if_py3(data).strip()
            if data:
                results.append(data)
        return results
