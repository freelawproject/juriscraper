# Scraper for Florida 4th District Court of Appeal Written Opinions
# CourtID: flaapp4written
# Court Short Name: flaapp4written
# Contact: Errors can be reported to Laura or Brandon, who are the
#  computer people for the court. The phone number is (561) 242-2000

from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.string_utils import convert_date_string


class Site(OpinionSite):
    """Web Interface: http://www.4dca.org/opinions_auto/most_recent_written.shtml"""

    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.set_url("o")

    def set_url(self, type):
        self.url = "https://edca.4dca.org/opinions.aspx?type=%s" % type

    def _get_docket_numbers(self):
        return self.return_text_for_cell(1)

    def _get_case_names(self):
        return self.return_text_for_cell(3)

    def _get_dispositions(self):
        return self.return_text_for_cell(5)

    def _get_download_urls(self):
        path = "%s/a/@href" % self.cell_path(2)
        return [href for href in self.html.xpath(path)]

    def _get_case_dates(self):
        return [
            convert_date_string(date_string)
            for date_string in self.return_text_for_cell(6)
        ]

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_dates)

    def return_text_for_cell(self, cell_number):
        return [
            cell.text_content().strip()
            for cell in self.html.xpath(self.cell_path(cell_number))
        ]

    def cell_path(self, cell_number):
        return '//table[@id="grdOpinions"]//td[%d]' % cell_number
