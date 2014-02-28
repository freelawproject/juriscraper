# Author: V. David Zvenyach
# Date created:2014-02-27

import time
from datetime import date
from datetime import datetime
from lxml import html
import re

from juriscraper.GenericSite import GenericSite
from juriscraper.lib.string_utils import titlecase


class Site(GenericSite):
    def __init__(self):
        super(Site, self).__init__()
        self.court_id = self.__module__
        self.url = 'https://ecf.dcd.uscourts.gov/cgi-bin/Opinions.pl?2014'

# <tr><td>02/26/2014<!-- dm=3921285,cs=25638 --></td><td>Criminal No. 1981-0306<br />USA v. HINCKLEY</td><td>Doc No. <a href='show_public_doc?1981cr0306-455' target='_blank'>455</a> (order)<br />Doc No. <a href='show_public_doc?1981cr0306-456' target='_blank'>456</a> (memorandum opinion and order)<br />&#160; by Judge Paul L. Friedman</td></tr>

    #Note: this gets the *last* order, assuming that the second is the Memorandum Order and Opinion if there are two documents listed.
    def _get_download_urls(self):
        return [t for t in self.html.xpath('//table[2]//tr[position()>0]/td[3]/a[last()]/@href')]

# TODO
#    def _get_judges(self):
#        return [re.sub('by ','',str(t)) for t in self.html.xpath(']')]
# Judge Name : 

    def _get_case_names(self):
        return [titlecase(t) for t in self.html.xpath('//table[2]//tr[position()>0]/td[2]//text()[preceding-sibling::br]')]

    # (e.g., 02/26/2014)
    def _get_case_dates(self):
        return [date.fromtimestamp(time.mktime(time.strptime(date_string, '%m/%d/%Y'))) for date_string in self.html.xpath('//table[2]//tr[position()>0]/td[1]//text()')]
 
    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_names)

    def _get_docket_numbers(self):
        return [t for t in self.html.xpath('//table[2]//tr[position()>0]/td[2]/br//preceding-sibling::text()[1]')]