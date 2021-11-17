# Scraper for Florida 1st District Court of Appeal Per Curiam
# CourtID: flaapp1
# Court Short Name: flaapp1

from datetime import date

from juriscraper.AbstractSite import logger
from juriscraper.lib.string_utils import convert_date_string
from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.court_number = 1
        self.type_id = 0  # Per Curiam
        self.url = self.get_url()
        self.back_scrape_iterable = [
            (12, 2012),
            (1, 2013),
            (2, 2013),
            (3, 2013),
            (4, 2013),
            (5, 2013),
            (6, 2013),
            (7, 2013),
            (8, 2013),
            (9, 2013),
            (10, 2013),
            (11, 2013),
            (12, 2013),
            (1, 2014),
            (2, 2014),
            (3, 2014),
            (4, 2014),
            (5, 2014),
            (6, 2014),
            (7, 2014),
            (8, 2014),
            (9, 2014),
            (10, 2014),
            (11, 2014),
            (12, 2014),
            (1, 2015),
            (2, 2015),
            (3, 2015),
            (4, 2015),
            (5, 2015),
            (6, 2015),
            (7, 2015),
            (8, 2015),
            (9, 2015),
            (10, 2015),
            (11, 2015),
            (12, 2015),
            (1, 2016),
            (2, 2016),
            (3, 2016),
            (4, 2016),
            (5, 2016),
            (6, 2016),
            (7, 2016),
            (8, 2016),
            (9, 2016),
            (10, 2016),
            (11, 2016),
            (12, 2016),
            (1, 2017),
            (2, 2017),
            (3, 2017),
            (4, 2017),
            (5, 2017),
            (6, 2017),
            (7, 2017),
            (8, 2017),
            (9, 2017),
            (10, 2017),
            (11, 2017),
            (12, 2017),
            (1, 2018),
            (2, 2018),
        ]

    def _get_case_names(self):
        return self.get_cell_content(3)

    def _get_download_urls(self):
        return self.get_cell_content(2, "//a/@href")

    def _get_case_dates(self):
        return [convert_date_string(ds) for ds in self.get_cell_content(6)]

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_dates)

    def _get_docket_numbers(self):
        return self.get_cell_content(1)

    def _get_dispositions(self):
        return self.get_cell_content(5)

    def _download_backwards(self, page_month_year):
        month = page_month_year[0]
        year = page_month_year[1]
        self.url = self.get_url(month, year)
        logger.info(f"Back scraping: {self.url}")
        self.html = self._download()

    def get_cell_content(self, cell_num, sub_path=False):
        path = '//table[@id="grdOpinions"]//tr/td[%d]' % cell_num
        cells = self.html.xpath(path + sub_path if sub_path else path)
        return (
            cells
            if sub_path
            else [cell.text_content().strip() for cell in cells]
        )

    def get_url(self, month=False, year=False):
        month = month if month else date.today().month
        year = year if year else date.today().year
        return (
            "https://edca.%ddca.org/Opinions.aspx?TypeID=%d&Day=All&Month=%d&Year=%d"
            % (self.court_number, self.type_id, month, year)
        )
