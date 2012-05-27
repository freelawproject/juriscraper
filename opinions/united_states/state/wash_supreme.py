from GenericSite import GenericSite
import re
import time
from datetime import date


class Site(GenericSite):
    def __init__(self):
        super(Site, self).__init__()
        self.url = (
        'http://www.courts.wa.gov/opinions/rssSCOpinionsFeed.cfm')
        self.court_id = self.__module__

    def _get_case_names(self):
        case_names = []
        for name in self.html.xpath(
        '/html/body/rss/channel/item/title/text()'):
            case_names.append(name.split(' -- ')[1])
        return case_names

    def _get_download_urls(self):
        urls = []
        for t in self.html.xpath(
        "/html/body/rss/channel/item/description/text()"):
            link = re.search(r'a href="(.*)"', t)
            urls.append(link.groups()[0])
        return urls

    def _get_docket_numbers(self):
        docket_numbers = []
        for name in self.html.xpath(
        '/html/body/rss/channel/item/title/text()'):
            docket_numbers.append(name.split(' -- ')[0])
        return docket_numbers

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_names)

    # Should concurrances and dissents be returned? As it stands, they are.
