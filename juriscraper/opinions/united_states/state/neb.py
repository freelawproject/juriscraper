# Author: Michael Lissner
# Date created: 2013-06-13

from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.string_utils import convert_date_string


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = 'https://supremecourt.nebraska.gov/courts/supreme-court/opinions'

    def _get_download_urls(self):
        return [href for href in self.html.xpath('//td[3]/a/@href')]

    def _get_case_names(self):
        return [cell.text_content() for cell in self.html.xpath('//td[3]')]

    def _get_case_dates(self):
        dates = []
        path_group = '//div[@class="view-grouping"]'
        subpath_date = './/span[@class="date-display-single"]'
        subpath_cases = './/tbody/tr'
        for group in self.html.xpath(path_group):
            date_string = group.xpath(subpath_date)[0].text_content()
            date = convert_date_string(date_string)
            case_count = len(group.xpath(subpath_cases))
            dates.extend([date] * case_count)
        return dates

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_names)

    def _get_docket_numbers(self):
        return [cell.text_content() for cell in self.html.xpath('//td[1]')]

    def _get_neutral_citations(self):
        return [cell.text_content() for cell in self.html.xpath('//td[2]')]