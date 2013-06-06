'''
History:
 - Left message for Diana Norman (512) 463-1551, at the Appeals Court, requesting a call back.

http://www.search.txcourts.gov/RetrieveDocument.aspx?DocId=886&Index=***coa01%5cOpinion
http://www.search.txcourts.gov/SearchMedia.aspx?MediaVersionID=906eee9d-85e3-48a8-9349-7387948b6673&coa=coa01&DT=Opinion&MediaID=cf67a534-225a-4a5e-966f-41f68c35e6c4
'''

# Author: Michael Lissner
# Date created: 2013-06-05

# import re
import requests
import time
from datetime import date
from lxml import html


from juriscraper.GenericSite import GenericSite
from juriscraper.YieldingList import YieldingList
# from juriscraper.lib.string_utils import titlecase


class Site(GenericSite):
    def __init__(self):
        super(Site, self).__init__()
        self.court_id = self.__module__
        self.url = 'http://www.search.txcourts.gov/Docket.aspx?coa=cossup&FullDate=5/24/2013'

    def _get_download_urls(self):
        '''Here we get very crafty, and create a custom list object.'''
        path = '//a[contains(@id, "lnkCase")]/@href'

        def fetcher(url):
            print "Visiting deferred URL: %s" % url
            r = requests.get(url,
                             allow_redirects=False,
                             headers={'User-Agent': 'Juriscraper'})
            # Throw an error if a bad status code is returned.
            r.raise_for_status()

            html_tree = html.fromstring(r.text)
            html_tree.make_links_absolute(self.url)

            # Path: href attr of the first tr that has an ancestor of type tr which in turn has a td containing the text
            # 'Opinion issued'
            path = "//tr[td/text()[contains(., 'Opinion issued')]]//tr[1]//@href"
            return html_tree.xpath(path)[0]

        urls = YieldingList(seed=self.html.xpath(path),
                            fetcher=fetcher)
        return urls



    def _get_case_names(self):
        path = '//td[@class = "caseStyle"]/span/text()'
        return list(self.html.xpath(path))

    def _get_case_dates(self):
        return [date.today()] * len(self.case_names)

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
        return list(self.html.xpath(path))

    """
      Optional method used for downloading multiple pages of a court site.
    """
    def _download_backwards(self):
        """ This is a simple method that can be used to generate Site objects
            that can be used to paginate through a court's entire website.

            This method is usually called by a backscraper caller (see the
            one in CourtListener/alert/scrapers for details), and typically
            modifies aspects of the Site object's attributes such as Site.url.

            For a simple example of this in use see the implementation for
            michigan in opinions/united_states/state/mich.py.

            This can also be used to hold notes useful to future backscraper
            development.
        """
        pass
