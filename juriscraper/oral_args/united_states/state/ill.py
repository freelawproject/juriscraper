'''
CourtID: ill
Court Short Name: Ill.
Author: Rebecca Fordon
Reviewer: 
History:
* 2016-06-22: Created by Rebecca Fordon
'''

from datetime import datetime
import re
from juriscraper.OralArgumentSite import OralArgumentSite


class Site(OralArgumentSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = 'http://www.illinoiscourts.gov/Media/On_Demand.asp' 

    def _get_download_urls(self):
        path = "//table[4]//table//tr[position()>1]/td[6]//a/@href"
        return list(self.html.xpath(path))

    def _get_case_dates(self):
        dates = []
        path = "//table[4]//table//tr[position()>1]/td[1]//div/text()"
        for s in self.html.xpath(path):
            date_format = '%m/%d/%y'
            try: 
                d = datetime.strptime(s, date_format).date()
                dates.append(d)
            except ValueError: 
                print(ValueError)
                print(s)
                continue
        return dates

    def _get_case_names(self):
        path = '//table[4]//table//tr[position()>1]/td[3]//div/text()'
        cases = []
        for case in self.html.xpath(path):
            if case.strip():
                cases.append(case)
        return cases

    def _get_docket_numbers(self):
        path = "//table[4]//table//tr[position()>1]/td[2]//div"  # right now this is giving a problem because one of the fields has a new line in the middle of it
        dockets = []
        for docket in self.html.xpath(path): 
            docket = docket.text_content() 
            dockets.append(docket)
        return dockets
