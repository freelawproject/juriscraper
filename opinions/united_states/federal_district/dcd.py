# Author: V. David Zvenyach
# Date created:2014-02-27

import time
from datetime import date
from datetime import datetime
from lxml import html
import re

from juriscraper.GenericSite import GenericSite
from juriscraper.lib.string_utils import titlecase

# TODO
# [x] Fix current year. (We don't hardcode the current year into a URL if we can help it. Other scrapers here can show you how to get the current year via a python method, and create a variable equal to that, then use the variable in the URL. This means that when 2015 rolls around, this scraper still works and no one has to go fix the URL.)
# [x] It is unfortunate that they put multiple documents in the same cell, but your solution to assume the last one is the opinion and just retrieve it, is both inaccurate on the current page, and not our preference. We want everything. So, we have to look at each row, determine if there are multiple docs, and if so, pad/repeat the case name and date fields to match, and retrieve every document. This is somewhat similar to what is done in the alaska.py scraper which lists multiple opinions under a single date.
# [x] You list the judge section as TO DO. Let's finish it. If you have the data from that cell via an xpath like //table[2]/tbody/tr/td[3] then we just need a regex like "by .*" that would get the judge name. They consistently use "by [Judge's Name]" so I think we can look for "by" and then chop that "by" off with python afterward. Again, the multiple docs per cell will mean that this field too needs to take that into account to get equal metadata for every field.
# [x] I think it's OK to leave "Civil" and "Criminal" in the docket number field, but it presents an opportunity to put that information into our nature_of_suit field. I might do this by just retrieving the docket #s again and then adding a little conditional check for Civil/Criminal and adding whatever you find to the nature_of_suit field.

class Site(GenericSite):
    def __init__(self):
        super(Site, self).__init__()
        self.court_id = self.__module__
        self.url = 'https://ecf.dcd.uscourts.gov/cgi-bin/Opinions.pl?' + str(date.today().year)

# <tr><td>02/26/2014<!-- dm=3921285,cs=25638 --></td><td>Criminal No. 1981-0306<br />USA v. HINCKLEY</td><td>Doc No. <a href='show_public_doc?1981cr0306-455' target='_blank'>455</a> (order)<br />Doc No. <a href='show_public_doc?1981cr0306-456' target='_blank'>456</a> (memorandum opinion and order)<br />&#160; by Judge Paul L. Friedman</td></tr>

    #Note: this returns, for each case, an array of urls for each listed object (e.g., memorandum opinion; order).
    def _get_download_urls(self):
        case_urls = []
        for case in self.html.xpath('//table[2]//tr[position()>0]/td[3]'):
            urls = case.xpath('./a/@href')
            case_urls.append(urls)
        return case_urls

    def _get_docket_document_numbers(self):
        documents = []
        for case in self.html.xpath('//table[2]//tr[position()>0]/td[3]'):
            urls = case.xpath('./a/@href')
            doc_no = []
            for url in urls:
                # We can infer both the nature of suit AND the docket number from the URL
                url_str = re.search(r'(\?)(\d+)([a-z]+)(\d+)(\-)(.*)',url)
                doc_no.append(url_str.group(6))
            documents.append(doc_no)
        return documents

    def _get_judges(self):
        judges = []
        for t in self.html.xpath('//table[2]//tr[position()>0]/td[3]'):
            judge_str = re.search(r'(by\s)(.*)(\<\/td\>)', html.tostring(t));
            judges.append(judge_str.group(2))
        return judges

    def _get_case_names(self):
        return [titlecase(t) for t in self.html.xpath('//table[2]//tr[position()>0]/td[2]//text()[preceding-sibling::br]')]
    def _get_case_dates(self):
        return [date.fromtimestamp(time.mktime(time.strptime(date_string, '%m/%d/%Y'))) for date_string in self.html.xpath('//table[2]//tr[position()>0]/td[1]//text()')]
 
    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_names)

    def _get_nature_of_suit(self):
        documents = []
        for case in self.html.xpath('//table[2]//tr[position()>0]/td[3]'):
            urls = case.xpath('./a/@href')
            doc_nature = []
            for url in urls:
                # We can infer both the nature of suit AND the docket number from the URL
                url_str = re.search(r'(\?)(\d+)([a-z]+)(\d+)(\-)(.*)',url)
                nature_code = url_str.group(3)
                if nature_code == 'cv':
                    doc_nature.append("Civil")
                elif nature_code == 'cr':
                    doc_nature.append("Criminal")
                else:
                    doc_nature.append("Other")
            documents.append(doc_nature[0])
        return documents