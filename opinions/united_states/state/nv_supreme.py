from GenericSite import GenericSite
import re
import time
from datetime import date


class Site(GenericSite):
    def __init__(self):
        super(Site, self).__init__()
        self.url = (
        'http://www.nevadajudiciary.us/index.php/advancedopinions')
        self.court_id = self.__module__

    def _get_case_names(self):
        return [name for name in self.html.
            xpath('//form[@name="adminForm"]/table//tr[@class]/td/a/text()')]

    #Link for each decision points to html page, not pdf. Target page has link to pdf, but scanned