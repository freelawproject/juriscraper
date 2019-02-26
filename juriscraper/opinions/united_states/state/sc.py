"""Scraper for South Carolina Supreme Court
CourtID: sc
Court Short Name: S.C.
Author: TBM <-- Who art thou TBM? ONLY MLR gets to be initials!
History:
 - 04-18-2014: Created.
 - 09-18-2014: Updated by mlr.
 - 10-17-2014: Updated by mlr to fix InsanityError
 - 2017-10-04: Updated by mlr to deal with their anti-bot system. Crux of change
               is to ensure that we get a cookie in our session by visiting the
               homepage before we go and scrape. Dumb.
 - 2019-02-26: Restructured completely by arderyp

Contact information:
 - Help desk: (803) 734-1193, Travis
 - Security desk: 803-734-5906, Joe Hilke
 - Web Developer (who can help with firewall issues): 803-734-0373, Winkie Clark
"""

from datetime import date

from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.exceptions import InsanityException
from juriscraper.lib.string_utils import convert_date_string


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        today = date.today()
        self.url = 'http://www.sccourts.org/opinions/indexSCPub.cfm?year=%d&month=%d' % (today.year, today.month)
        self.cases = []

    def _process_html(self):
        path = '//a[@class="blueLink2"][contains(./@href, ".pdf") or contains(./@href, "?orderNo=")]'
        for link in self.html.xpath(path):
            url = link.attrib['href']
            text = link.text_content().strip()
            parts = text.split('-', 1)
            docket = parts[0].strip()
            docket = '' if 'order' in docket.lower() else docket
            name = parts[1]
            parent = link.getparent()
            parents_parent = parent.getparent()
            attributes_parent = parent.attrib
            attributes_parents_parent = parents_parent.attrib
            container_id = 'maincontent'
            if 'id' in attributes_parent and attributes_parent['id'] == container_id:
                search_root = link
            elif 'id' in attributes_parents_parent and attributes_parents_parent['id'] == container_id:
                search_root = parent
            else:
                # Link should be within a <p> tag directly under <div id='maincontent'>, but
                # occasionally the courts forgets the wrap it in a <p>, in which case it should
                # be directly under the <div id='maincontent'>
                raise InsanityException('Unrecognized placement of Opinion url on page: "%s"' % text)
            date_element = search_root.xpath('./preceding-sibling::b')[0]
            date_element_text = date_element.text_content().strip().lower()
            if not date_element_text.endswith('opinions') and not date_element_text.endswith('orders'):
                # text should be like "5-14-2014 - Opinions" or "5-21-2014 - Orders"
                raise InsanityException('Unrecognized bold (date) element: "%s"' % date_element_text)
            date_string = date_element_text.split()[0]

            self.cases.append({
                'date': convert_date_string(date_string),
                'name': name,
                'docket': docket,
                'url': url,
            })

    def _get_download_urls(self):
        return [case['url'] for case in self.cases]

    def _get_case_names(self):
        return [case['name'] for case in self.cases]

    def _get_case_dates(self):
        return [case['date'] for case in self.cases]

    def _get_docket_numbers(self):
        return [case['docket'] for case in self.cases]

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.cases)
