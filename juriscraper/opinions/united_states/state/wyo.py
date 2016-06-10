"""Scraper for Wyoming Supreme Court
CourtID: wyo
Court Short Name: Wyo.
History:
 - 2014-07-02: mlr: Created new version when court got new website.
 - 2015-07-06: m4h7: Updated to use JSON!
 - 2016-06-09: arderyp: Updated because json endpoint moved and was changed
"""

import re
from datetime import datetime

from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.base_url = 'http://www.courts.state.wy.us'
        self.url = self.base_url + '/Supreme/OpinionsVM?EndDate=12%2F27%2F2014&StartDate=2%2F27%2F2006'
        self.court_id = self.__module__

    def _get_case_names(self):
        case_names = []
        for record in self.html:
            case_names.append('%s v. %s' % (record['Appellant'], record['Appellee']))
        return case_names

    def _get_download_urls(self):
        download_urls = []
        for record in self.html:
            pdf_file_name = record['DocumentName']
            if pdf_file_name[:5] == '../..':
                pdf_file_name = pdf_file_name[5:]
            url = self.base_url + '/Documents/Opinions/' + pdf_file_name
            download_urls.append(url)
        return download_urls

    def _get_case_dates(self):
        case_dates = []
        date_re = re.compile(r"^/Date\((\d+)\)/$")
        for record in self.html:
            m = date_re.match(record['date_heard'])
            if m:
                t = int(m.group(1)) / 1000
                case_dates.append(datetime.fromtimestamp(t).date())
        return case_dates

    def _get_docket_numbers(self):
        return [record['DocketNumber'] for record in self.html]

    def _get_neutral_citations(self):
        return [record['OpinionID'] for record in self.html]

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_names)
