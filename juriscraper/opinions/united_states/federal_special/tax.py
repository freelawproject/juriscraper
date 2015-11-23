# Scraper for the United States Tax Court
# CourtID: tax
# Court Short Name: Tax Ct.
# Neutral Citation Format (Tax Court opinions): 138 T.C. No. 1 (2012)
# Neutral Citation Format (Memorandum opinions): T.C. Memo 2012-1
# Neutral Citation Format (Summary opinions: T.C. Summary Opinion 2012-1

from datetime import datetime

from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.url = 'http://www.ustaxcourt.gov/UstcInOp/asp/Todays.asp'
        self.use_sessions = True
        self.court_id = self.__module__

    def _get_download_urls(self):
        return [t for t in self.html.xpath('//*[@id="Content_pnlOpinions"]//table/tr[position() > 1]/td/a/@href')]

    def _get_case_names(self):
        case_names = []
        for t in self.html.xpath( '//*[@id="Content_pnlOpinions"]//table/tr[position() > 1]/td/a/text()'):
            case_names.append(t + ' v. Commissioner')
        return case_names

    def _get_precedential_statuses(self):
        statuses = []
        for t in self.html.xpath( '//*[@id="Content_pnlOpinions"]//table/tr[position() > 1]/td/a/@href'):
            if ".TC." in t:
                statuses.append('Published')
            elif ".TCM." in t:
                statuses.append('Published')
            elif ".SUM." in t:
                statuses.append('Unpublished')
            else:
                statuses.append('Unknown')
        return statuses

    def _get_case_dates(self):
        path = '//*[@id="Content_pnlOpinions"]//table/tr[position() > 1]/td[2]/text()'
        return [datetime.strptime(date_string, '%m/%d/%Y').date()
                for date_string in self.html.xpath(path)]
