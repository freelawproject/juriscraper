"""
History:
 - 2014-08-05: Adapted scraper to have year-based URLs.
"""

from juriscraper.OpinionSite import OpinionSite
import re
import time
from datetime import date


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.today = date.today()
        self.url = 'http://www.publications.ojd.state.or.us/Pages/OpinionsSC{year}.aspx'.format(year=self.today.year)
        # self.url = 'http://www.publications.ojd.state.or.us/Pages/OpinionsSC2014.aspx'
        self.court_id = self.__module__

    def _get_case_names(self):
        case_names = []
        for name in self.html.xpath("/html/body//h2[contains(.,'SUPREME')]/following-sibling::ul[1]/li/a//text()"):
            case_names.append(re.sub(r'\(?S\d+[\s)]\s?', '', name))
        return case_names

    def _get_docket_numbers(self):
        docket_numbers = []
        for s in self.html.xpath("/html/body//h2[contains(.,'SUPREME')]/following-sibling::ul[1]/li/a//text()"):
            docket_numbers.append(' & '.join(re.findall('S\d+', s)))
        return docket_numbers

    def _get_download_urls(self):
        return [t for t in self.html.xpath("/html/body//h2[contains(.,'SUPREME')]/following-sibling::ul[1]/li/a/@href")]

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
