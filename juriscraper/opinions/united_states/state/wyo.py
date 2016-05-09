"""Scraper for Wyoming Supreme Court
CourtID: wyo
Court Short Name: Wyo.
History:
 - 2014-07-02: mlr: Created new version when court got new website.
 - 2015-07-06: m4h7: Updated to use JSON!
"""

from datetime import datetime

from juriscraper.OpinionSite import OpinionSite
import re


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.base_url = 'http://www.courts.state.wy.us'
        self.url = self.base_url + '/Home/GetOpinions'
        self.court_id = self.__module__

    def _get_case_names(self):
        case_names = []
        for v in self.html['Data']:
            case_names.append('%s v. %s' % (v['appellant'], v['appellee']))
        return case_names

    def _get_download_urls(self):
        download_urls = []
        for v in self.html['Data']:
            relpath = v['DocumentName']
            if relpath[:5] == '../..':
                relpath = relpath[5:]
            url = self.base_url + relpath
            download_urls.append(url)
        return download_urls

    def _get_case_dates(self):
        case_dates = []
        date_re = re.compile(r"^/Date\((\d+)\)/$")
        for v in self.html['Data']:
            m = date_re.match(v['date_heard'])
            if m:
                t = int(m.group(1)) / 1000
                case_dates.append(datetime.fromtimestamp(t).date())
        return case_dates

    def _get_docket_numbers(self):
        return [v['DocketNumber'] for v in self.html['Data']]

    def _get_neutral_citations(self):
        return [v['OpinionID'] for v in self.html['Data']]

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_names)
