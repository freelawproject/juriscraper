# Scraper for Georgia Appeals Court
# CourtID: gactapp
# Court Short Name: gactapp
# Author: Andrei Chelaru
# Reviewer: mlr
# Date created: 25 July 2014


from datetime import date, timedelta
from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.string_utils import titlecase
from juriscraper.lib.string_utils import convert_date_string


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.case_date = date.today()
        self.a_while_ago = date.today() - timedelta(days=20)
        self.base_path = "id('art-main')//tr[position() > 1]"
        self.url = 'http://www.gaappeals.us/docketdate/results_all.php?searchterm=' \
                   '{mn_ago:02d}%2F{day_ago:02d}%2F{year_ago}&searchterm2=' \
                   '{mn:02d}%2F{day:02d}%2F{year}&submit=Search'.format(
            mn_ago=self.a_while_ago.month,
            day_ago=self.a_while_ago.day,
            year_ago=self.a_while_ago.year,
            mn=self.case_date.month,
            day=self.case_date.day,
            year=self.case_date.year,
        )

    def _download(self, request_dict={}):
        if self.method == 'LOCAL':
            # This is an arbitrary date that we need to set
            # for our compar.json test to pass
            self.case_date = convert_date_string('2017-08-14')
        return super(Site, self)._download(request_dict=request_dict)

    def _get_case_names(self):
        path = "{base}/td[2]/text()".format(base=self.base_path)
        return [titlecase(e) for e in self.html.xpath(path)]

    def _get_download_urls(self):
        path = "{base}/td[6]/a/@href".format(base=self.base_path)
        return list(self.html.xpath(path))

    def _get_case_dates(self):
        return [self.case_date] * int(self.html.xpath("count({base})".format(base=self.base_path)))

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_names)

    def _get_docket_numbers(self):
        path = "{base}/td[1]/text()".format(base=self.base_path)
        return list(self.html.xpath(path))

    def _get_dispositions(self):
        path = "{base}/td[4]/text()".format(base=self.base_path)
        return [titlecase(e) for e in self.html.xpath(path)]
