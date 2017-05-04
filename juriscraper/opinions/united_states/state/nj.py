# Author: Krist Jin
# Reviewer: mlr
# History:
#  - 2013-08-03: Created.
#  - 2014-08-05: Updated by mlr.
#  - 2017-05-03: arderyp fixed new bad html use case

from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.string_utils import titlecase, convert_date_string


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = 'http://www.judiciary.state.nj.us/opinions/index.htm'
        self.table = '1'  # Used as part of the paths to differentiate between appellate and supreme

    def _get_download_urls(self):
        """Court has bad html in some cases, so we
        need to iterate over each cell and extract
        the first href from an anchor with text content
        """
        urls = []
        path = '//*[@id="content2col"]/table[%s]/tr/td[3]' % self.table
        for cell in self.html.xpath(path):
            url_list = cell.xpath('.//a[text()]/@href')
            if url_list:
                urls.append(url_list[0])
        return urls

    def _get_case_names(self):
        titles = []
        path = '//*[@id="content2col"]/table[%s]/tr/td[3][.//a]' % self.table
        for element in self.html.xpath(path):
            title = ' '.join(element.text_content().upper().split())
            titles.append(titlecase(title))
        return titles

    def _get_case_dates(self):
        path = ('//*[@id="content2col"]/table[%s]/tr[.//a]/td[1]//text()' % self.table)
        return [convert_date_string(d.strip()) for d in self.html.xpath(path)]

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_names)

    def _get_docket_numbers(self):
        path = ('//*[@id="content2col"]/table[%s]/tr[.//a]/td[2]' % self.table)
        return [cell.text_content() for cell in self.html.xpath(path)]
