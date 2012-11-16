from juriscraper.GenericSite import GenericSite
import re
import time
from datetime import date
from lxml import html

'''
TODO:
 - Purge footnotess
 - Find the doc type
 - figure out how to handle HTML
'''


class Site(GenericSite):
    def __init__(self):
        super(Site, self).__init__()
        self.url = 'http://www.massreports.com/slipops/redirect.aspx?location=sjcopinions'
        #self.url = 'http://weblinks.westlaw.com/signon/default.wl?ACTION=SEARCH&bQlocfnd=True&clientid=massreports&DB=MA%2DORSLIP&frompool=1&Method=TNC&path=%2Fsearch%2Fdefault%2Ewl&pwd=%7EAEP8I%5E%3D5I%2B%3B%2Fa%5Dj%3E%3DQP%5F%5Bb%3DP%2FF%3F%5D%7D%60M%60&query=to%28allsct+allsctrs+allsctoj%29+&rs=MAOR1%2E0&sp=MassOF%2D1001&ssl=n&strRecreate=no&vr=1%2E0'
        self.court_id = self.__module__
        self.grouping_regex = re.compile("(.*)\.\w{3}(.*)\.\w{3}(.*)\.")

    def _download(self):
        import sys
        config = {'verbose': sys.stdout,
                  'User-Agent': 'Mozilla/5.0 (X11; Linux i686 on x86_64; rv:5.0a2) Gecko/20110524 Firefox/5.0a2'}
        return GenericSite._download(self, use_sessions=True, config=config)

    def _get_case_names(self):
        return [self.grouping_regex.search(s).group(1)
                for s in self.html.xpath('//span[@class[contains(.,"ResultSubListItem")]]/text()')]

    def _get_download_urls(self):
        return [a for a in self.html.xpath('//span[@class[contains(.,"Cite")]]/a/@href')]

    def _get_case_dates(self):
        dates = []
        for s in self.html.xpath('//span[@class[contains(.,"ResultSubListItem")]]/text()'):
            s = self.grouping_regex.search(s).group(3)
            dates.append(date.fromtimestamp(time.mktime(time.strptime(s, '%m %d, %Y'))))
        return dates

    def _get_docket_numbers(self):
        return [self.grouping_regex.search(s).group(2)
                for s in self.html.xpath('//span[@class[contains(.,"ResultSubListItem")]]/text()')]

    def _get_precedential_statuses(self):
        statuses = []
        for e in self.html.xpath("//item/category"):
            text = html.tostring(e, method='text').lower().strip()
            if "unpublished" in text:
                statuses.append("Unpublished")
            elif "published" in text:
                statuses.append("Published")
            elif "errata" in text:
                statuses.append("Errata")
            else:
                statuses.append("Unknown")
        return statuses
