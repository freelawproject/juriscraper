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

Contact information:
 - Help desk: (803) 734-1193, Travis
 - Security desk: 803-734-5906, Joe Hilke
 - Web Developer (who can help with firewall issues): 803-734-0373, Winkie Clark
"""

from datetime import date
from datetime import datetime

import re

from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        today = date.today()
        self.url = 'http://www.sccourts.org/opinions/indexSCPub.cfm?year=%d&month=%d' % (today.year, today.month)
        self.sc_homepage = 'http://www.sccourts.org'

    def _request_url_get(self, url):
        """SC has an annoying system that requires cookies to scrape.

        Therefore, before we scrape, we go and get some cookies.
        """
        self.request['session'].get(self.sc_homepage)
        self.request['url'] = url
        self.request['response'] = self.request['session'].get(
            url,
            headers=self.request['headers'],
            verify=self.request['verify'],
            timeout=60,
            **self.request['parameters']
        )

    def _get_download_urls(self):
        path = '//div[@id="pageContentOpinionList"]//a[contains(@href, "HTMLFiles") or contains(@href, "courtOrders")]/@href'
        return list(self.html.xpath(path))

    def _get_case_names(self):
        case_names = []
        path = '//div[@id="pageContentOpinionList"]//a[contains(@href, "HTMLFiles") or contains(@href, "courtOrders")]/text()'
        for txt in self.html.xpath(path):
            expression = '(.* - )(.*)'
            case_name = re.search(expression, txt, re.MULTILINE).group(2)
            case_names.append(case_name)
        return case_names

    def _get_case_dates(self):
        dates = []
        for node in self.html.xpath('//div[@id="pageContentOpinionList"]/node()[not(self::text())]'):
            try:
                tag_name = node.tag
                if tag_name == 'b':
                    # It's a header, grab the date and reset the counter
                    date_obj = datetime.strptime(node.text.strip().split(' ', 1)[0],
                                                 '%m-%d-%Y').date()
                elif tag_name == 'a':
                    # If it's a link, we've already got the correct date, so each time we have a link, append it to
                    # our list.
                    dates.append(date_obj)
                else:
                    continue
            except AttributeError:
                # Text node; something else
                tag_name = None  # Not essential, but reset this for the next iteration of the loop
                continue

        return dates

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_names)

    def _get_docket_numbers(self):
        docket_numbers = []
        path = '//div[@id="pageContentOpinionList"]//a[contains(@href, "HTMLFiles") or contains(@href, "courtOrders")]/text()'
        for txt in self.html.xpath(path):
            expression = '(.* - )(.*)'
            docket_number = re.search(expression, txt,
                                      re.MULTILINE).group(1)
            if 'order' in docket_number.lower():
                docket_number = ''
            docket_numbers.append(docket_number)
        return docket_numbers
