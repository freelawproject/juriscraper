from GenericSite import GenericSite
import re
import time
from datetime import date


class Site(GenericSite):
    def __init__(self):
        super(Site, self).__init__()
        self.url = (
        'http://courts.oregon.gov/Publications/OpinionsSC.page')
        self.court_id = self.__module__

    def _get_case_names(self):
        case_names = []
        for name in self.html.xpath(
        "/html/body//h2[contains(.,'SUPREME')]"
        "/following-sibling::ul[1]/li/a//text()"):
            try:
                case_names.append(re.sub('\(?S\d+[\s\)]\s?', '', name))
            except IndexError:
                print('Error with ' + name)
        return case_names

    def _get_download_urls(self):
        return [t for t in self.html.
                xpath(
                "/html/body//h2[contains(.,'SUPREME')]"
                "/following-sibling::ul[1]/li/a/@href")]

    def _get_case_dates(self):
        dates = []
        for opinion in self.html.xpath(
        '/html/body//h2[contains(.,"SUPREME")]'
            '/following-sibling::ul[1]/li[a/@href]'):
            for d in opinion.xpath('parent::ul'
            '/preceding-sibling::*[1]//text()[normalize-space(.) != ""]'):
                normalizedDate = self._normalizeDateString(d)
                dates.append(date.fromtimestamp
                (time.mktime(time.strptime(normalizedDate, '%m/%d/%Y'))))
        return dates

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_names)

    def _normalizeDateString(self, date):

        dateComponents = date.split('/')

        properYearStringLength = 4
        properMonthDayStringLength = 2
        yearPosition = 2

        for position, dateComponent in enumerate(dateComponents):
            if position != yearPosition and len(
            dateComponent) < properMonthDayStringLength:
                dateComponents[position] = '0' + dateComponent
            if position == yearPosition and len(
            dateComponent) < properYearStringLength:
                if int(dateComponent) > 50:
                    dateComponents[position] = '19' + dateComponent
                else:
                    dateComponents[position] = '20' + dateComponent
        return '/'.join(dateComponents)
