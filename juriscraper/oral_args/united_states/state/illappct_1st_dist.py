'''
CourtID: illappct
Court Short Name: Ill. App. Ct.
Author: Rebecca Fordon
Reviewer: 
History:
* 2016-06-23: Created by Rebecca Fordon
'''

from datetime import datetime
from juriscraper.OralArgumentSite import OralArgumentSite


class Site(OralArgumentSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = 'http://www.illinoiscourts.gov/Media/Appellate/1st_District.asp' 

    def _get_download_urls(self):
        path = "//table//table[2]/tr/td/table//tr[2]/td//tr[position()>1]//a/@href"
        return list(self.html.xpath(path))

    def _get_case_dates(self):
        dates = []
        path = "//table//table[2]/tr/td/table//tr[2]/td//tr[position()>1]/td[1]//div"
        for s in self.html.xpath(path):
            s = s.text_content() # necessary because some fields have breaks within the field
            s = s.split()[0] # the string contains info not relevant to the date, so this strips off the remainder of string after the date
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
        path = '//table//table[2]/tr/td/table//tr[2]/td//tr[position()>1]/td[4]//div/text()'
        cases = []
        for case in self.html.xpath(path):
            if case.strip():
                cases.append(case)
        return cases

    def _get_docket_numbers(self):
        path = "//table//table[2]/tr/td/table//tr[2]/td//tr[position()>1]/td[3]//div"  
        dockets = []
        # necessary because some fields have breaks within the field
        for docket in self.html.xpath(path): 
            docket = docket.text_content() 
            dockets.append(docket)
        return dockets
