from juriscraper.GenericSite import GenericSite
import re
import time
from datetime import date


class Site(GenericSite):
    def __init__(self):
        super(Site, self).__init__()
        self.url = 'http://www.publications.ojd.state.or.us/Pages/OpinionsSC.aspx'
        self.court_id = self.__module__

    def _get_case_names(self):
        case_names = []
        for name in self.html.xpath("/html/body//h2[contains(.,'SUPREME')]"
                                    "/following-sibling::ul[1]/li/a//text()"):
            case_names.append(re.sub('\(?S\d+[\s\)]\s?', '', name))
        return case_names

    def _get_download_urls(self):
        return [t for t in self.html.xpath("/html/body//h2[contains(.,'SUPREME')]"
                                           "/following-sibling::ul[1]/li/a/@href")]

    def _get_case_dates(self):
        dates = []
        for opinion in self.html.xpath('/html/body//h2[contains(.,"SUPREME")]'
                                       '/following-sibling::ul[1]/li[a/@href]'):
            for d in opinion.xpath('parent::ul/preceding-sibling::*[1]//'
                                   'text()[normalize-space(.) != ""]'):
                try:
                    t = time.strptime(d, '%m/%d/%y')
                except ValueError:
                    t = time.strptime(d, '%m/%d/%Y')
                dates.append(date.fromtimestamp(time.mktime(t)))
        return dates

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_names)
