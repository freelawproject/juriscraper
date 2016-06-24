'''
CourtID: ill
Court Short Name: Ill.
Author: Rebecca Fordon
Reviewer: Mike Lissner
History:
* 2016-06-22: Created by Rebecca Fordon
'''

from datetime import datetime
from juriscraper.OralArgumentSite import OralArgumentSite


class Site(OralArgumentSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = 'http://www.illinoiscourts.gov/Media/On_Demand.asp'
        self.xpath_root = '(//table[@id="nicetable"])[2]//tr[position() > 1]'

    def _get_download_urls(self):
        path = self.xpath_root + "/td[6]//@href"
        return list(self.html.xpath(path))

    def _get_case_dates(self):
        dates = []
        path = self.xpath_root + "/td[1]//text()"
        for s in self.html.xpath(path):
            try:
                d = datetime.strptime(s, '%m/%d/%y').date()
            except ValueError:
                continue
            else:
                dates.append(d)
        return dates

    def _get_case_names(self):
        path = self.xpath_root + '/td[3]//text()'
        cases = []
        for case in self.html.xpath(path):
            if case.strip():
                cases.append(case)
        return cases

    def _get_docket_numbers(self):
        path = self.xpath_root + "/td[2]"
        dockets = []
        for docket in self.html.xpath(path):
            docket = docket.text_content()
            dockets.append(docket)
        return dockets
