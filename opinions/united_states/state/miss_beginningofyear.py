# Auth: mlr
# Date: 2013-04-26

import miss
from datetime import date
from lxml import html

class Site(miss.Site):
    def __init__(self):
        super(Site, self).__init__()
        self.court_id = self.__module__

        # If it's the beginning of January, we need to make sure that we aren't
        # missing any late-coming cases from the previous year. 
        today = date.today()
        if today.day < 15 and today.month == 1:
            year = today.year - 1
            self.url = 'http://courts.ms.gov/scripts/websiteX_cgi.exe/GetOpinion?Year=%s&Court=Supreme+Court&Submit=Submit' % year
        else:
            # This simply aborts the crawler.
            self.status = 200
            self.html = html.fromstring('<html></html>')
