'''
History:
 - Left message for Diana Norman (512) 463-1551, at the Appeals Court, requesting a call back.

http://www.search.txcourts.gov/RetrieveDocument.aspx?DocId=886&Index=***coa01%5cOpinion
http://www.search.txcourts.gov/SearchMedia.aspx?MediaVersionID=906eee9d-85e3-48a8-9349-7387948b6673&coa=coa01&DT=Opinion&MediaID=cf67a534-225a-4a5e-966f-41f68c35e6c4
'''

# Author: Michael Lissner
# Date created: 2013-06-05

import requests
from datetime import date
from datetime import datetime
from lxml import html


from juriscraper.GenericSite import GenericSite
from juriscraper.DeferringList import DeferringList
from juriscraper.lib.string_utils import titlecase


class Site(GenericSite):
    def __init__(self):
        super(Site, self).__init__()
        self.court_id = self.__module__
        today = date.today()
        self.url = 'http://www.search.txcourts.gov/Docket.aspx?coa=cossup&FullDate=%s' % (today.strftime("%m/%d/%Y"))
        # for testing
        #self.url = 'http://www.search.txcourts.gov/Docket.aspx?coa=cossup&FullDate=5/24/2013'

    def _get_download_urls(self):
        '''Here we get very crafty and create a list-like object with deferred fetching.'''
        def fetcher(url):
            r = requests.get(url,
                             allow_redirects=False,
                             headers={'User-Agent': 'Juriscraper'})
            # Throw an error if a bad status code is returned.
            r.raise_for_status()

            html_tree = html.fromstring(r.text)
            html_tree.make_links_absolute(self.url)

            paths = ["//tr[td/text()[contains(., 'Opinion issued')]]//tr[descendant::a[contains(., 'HTML')]]//@href",
                     "//tr[td/text()[contains(., 'Opinion issued')]]//tr[descendant::a[contains(., 'PDF')]]//@href"]
            url = None
            for path in paths:
                try:
                    url = html_tree.xpath(path)[0]
                    break
                except IndexError:
                    continue
            return url

        path = '//a[contains(@id, "lnkCase")]/@href'
        seed_urls = self.html.xpath(path)
        if seed_urls:
            urls = DeferringList(seed=seed_urls, fetcher=fetcher)
            return urls
        else:
            return []

    def _get_case_names(self):
        path = '//td[@class = "caseStyle"]/span/text()'
        return [titlecase(s) for s in self.html.xpath(path)]

    def _get_case_dates(self):
        date_str = self.html.xpath("//span[@id = 'ctl00_ContentPlaceHolder1_lblDocketDate']/text()")[0]
        dt = datetime.strptime(date_str, "%m/%d/%Y").date()

        # Uses the path from the case_name as a multiplier, since case_names are not known when case_date is run.
        path = '//td[@class = "caseStyle"]/span/text()'
        return [dt] * len(list(self.html.xpath(path)))

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_names)

    def _get_docket_numbers(self):
        path = '//a[contains(@id, "lnkCase")]/text()'
        return list(self.html.xpath(path))

    def _get_lower_courts(self):
        path = "//td[@class = 'caseStyle']/text()"
        return list(self.html.xpath(path))

    def _get_dispositions(self):
        path = "//td[@class = 'caseDisp']/text()"
        return [titlecase(s) for s in self.html.xpath(path)]

    def _download_backwards(self, d):
        self.url = 'http://www.search.txcourts.gov/Docket.aspx?coa=cossup&FullDate=%s' % (d.strftime("%m/%d/%Y"))
        self.html = self._download()
