'''
CourtID: illappct
Court Short Name: Ill. App. Ct.
Author: Rebecca Fordon
Reviewer: Mike Lissner
History:
* 2016-06-23: Created by Rebecca Fordon
'''

import ill


class Site(ill.Site):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = 'http://www.illinoiscourts.gov/Media/Appellate/Workers_Comp.asp'
        self.xpath_root = '(//table[@class="nicetable"])[2]//tr[position() > 1]'
        self.download_url_path = '/td[5]//@href'
        self.case_name_path = '/td[3]//div/text()'
        self.docket_number_path = "/td[2]"
        self.back_scrape_iterable = range(2009, 2016)
