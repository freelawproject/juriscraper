# Author: Michael Lissner
# History:
# - 2013-06-03, mlr: Created
# - 2014-08-06, mlr: Updated for new website
# - 2015-07-30, mlr: Updated for changed website (failing xpaths)

from datetime import datetime

from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.string_utils import clean_if_py3


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = 'http://nvcourts.gov/Supreme/Decisions/Advance_Opinions/'
        self.xpath_adjustment = 0
        self.table_number = 2
        self.base_path = '(//table)[{table_number}]//td[{i}]'
        self.date_path = self._make_date_path()

    def _make_date_path(self):
        """Needed so that subclasses can make a date path as part of their
         init process
         """
        return '{base}//text()[normalize-space(.)]'.format(
            base=self.base_path.format(
                table_number=self.table_number,
                i=4 + self.xpath_adjustment,
            ),
        )

    def _get_download_urls(self):
        path = '{base}//@href'.format(
            base=self.base_path.format(
                table_number=self.table_number,
                i=4 + self.xpath_adjustment,
            ),
        )
        return list(self.html.xpath(path))

    def _get_case_names(self):
        path = '{base}//text()'.format(
            base=self.base_path.format(
                table_number=self.table_number,
                i=3 + self.xpath_adjustment,
            ),
        )
        return list(self.html.xpath(path))

    def _get_case_dates(self):
        case_dates = []
        for el in self.html.xpath(self.date_path):
            date_string = clean_if_py3(str(el)).strip()
            if date_string:
                case_dates.append(datetime.strptime(date_string, '%b %d, %Y').date())

        return case_dates

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_names)

    def _get_docket_numbers(self):
        path = '{base}//text()[normalize-space(.)]'.format(
            base=self.base_path.format(
                table_number=self.table_number,
                i=2 + self.xpath_adjustment,
            ),
        )
        docket_numbers = []
        for el in self.html.xpath(path):
            text = clean_if_py3(str(el)).strip()
            if text:
                docket_numbers.append(text)
        return docket_numbers

    def _get_neutral_citations(self):
        neutral_path = '{base}//text()'.format(
            base=self.base_path.format(
                table_number=self.table_number,
                i=1 + self.xpath_adjustment,
            ),
        )

        date_strings = []
        for el in self.html.xpath(self.date_path):
            date_string = clean_if_py3(str(el)).strip()
            if date_string:
                date_strings.append(date_string)

        neutral_citations = []
        for neutral_number, \
            date_string in zip(
                self.html.xpath(neutral_path),
                date_strings):
            year = datetime.strptime(date_string.strip(), '%b %d, %Y').year
            neutral_citations.append('{year} NV {num}'.format(year=year, num=neutral_number))
        return neutral_citations

