from juriscraper.OpinionSite import OpinionSite
from juriscraper.AbstractSite import logger
from juriscraper.lib.string_utils import convert_date_string


class Site(OpinionSite):
    CELLS = {
        'date': 2,
        'docket': 3,
        'name': 4,
        'revision': 5,
    }
    BASE_TABLE_ROW_PATH = '//div[@id = "mainbody"]//table//tr'

    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.url = 'http://www.supremecourt.gov/opinions/slipopinions.aspx'
        self.court_id = self.__module__
        self.back_scrape_url = 'http://www.supremecourt.gov/opinions/slipopinion/{}'
        self.back_scrape_iterable = range(6, 16)

    def _get_case_names(self):
        cell_sub_path = 'td[%d]/a/text()' % self.CELLS['name']
        case_names_path = '%s/%s' % (self.BASE_TABLE_ROW_PATH, cell_sub_path)
        case_names = self.html.xpath(case_names_path)

        # Append case name for revised opinion records
        for row in self._get_table_rows():
            if self._row_has_revision(row):
                case_names.append(row.xpath(cell_sub_path)[0])

        return case_names

    def _get_download_urls(self):
        return self._get_opinion_urls() + self._get_revision_urls()

    def _get_case_dates(self):
        return self._get_opinion_dates() + self._get_revision_dates()

    def _get_docket_numbers(self):
        cell_sub_path = 'td[%d]/text()' % self.CELLS['docket']
        dockets_path = '%s/%s' % (self.BASE_TABLE_ROW_PATH, cell_sub_path)
        docket_numbers = [docket_number for docket_number in self.html.xpath(dockets_path)]

        # Append docket number for revised opinion records
        for row in self._get_table_rows():
            if self._row_has_revision(row):
                docket_numbers.append(row.xpath(cell_sub_path)[0])

        return docket_numbers

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_names)

    def _download_backwards(self, d):
        logger.info("Running backscraper for year: 20{}".format(d))
        self.url = self.back_scrape_url.format(d if d >= 10 else '0{}'.format(d))
        self.html = self._download()
        if self.html is not None:
            # Setting status is important because it prevents the download
            # function from being run a second time by the parse method.
            self.status = 200

    def _get_opinion_dates(self):
        return self._get_dates_from_path('%s/td[%d]/text()' % (self.BASE_TABLE_ROW_PATH, self.CELLS['date']))

    def _get_revision_dates(self):
        return self._get_dates_from_path('%s/td[%d]/a/text()' % (self.BASE_TABLE_ROW_PATH, self.CELLS['revision']))

    def _get_dates_from_path(self, path):
        return [convert_date_string(date_string) for date_string in self.html.xpath(path)]

    def _get_opinion_urls(self):
        return self._get_url_from_cell_index(self.CELLS['name'])

    def _get_revision_urls(self):
        return self._get_url_from_cell_index(self.CELLS['revision'])

    def _get_url_from_cell_index(self, cell):
        path = '%s/td[%d]/a/@href' % (self.BASE_TABLE_ROW_PATH, cell)
        return [url for url in self.html.xpath(path)]

    def _row_has_revision(self, row):
        revision = row.xpath('td[%d]/a' % self.CELLS['revision'])
        return True if revision else False

    def _get_table_rows(self):
        return [row for row in self.html.xpath(self.BASE_TABLE_ROW_PATH) if len(row.xpath('td')) > 0]
