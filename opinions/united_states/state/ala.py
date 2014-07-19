"""Scraper for Alabama Supreme Court
CourtID: ala
Court Short Name: Ala. Sup. Ct.
Author: mlr
Reviewer: None
Date created: 2014-07-18
"""
from StringIO import StringIO
from juriscraper.DeferringList import DeferringList
import os
import re
from lxml import html

import requests
from datetime import datetime

from juriscraper.AbstractSite import logger
from juriscraper.OpinionSite import OpinionSite
from selenium import webdriver


class Site(OpinionSite):
    def __init__(self):
        super(Site, self).__init__()
        self.court_id = self.__module__
        self.url = 'http://2.alalinc.net/library/list/files/?lib=SUPREME'

    def _download(self, request_dict={}):
        """Alabama requires a login in order to work. Here, we login, set the cookies,
        and then run the usual download method.
        """
        r = requests.post(
            'http://2.alalinc.net/session/login/',
            data={'uid': 'justia', 'pwd': 'peace99'},
            headers={'User-Agent': 'Juriscraper'}
        )
        self._cookies = dict(r.cookies)
        return super(Site, self)._download(request_dict={'cookies': self._cookies})

    def _clean_text(self, text):
        """Alabama has some *nasty* code that generates an HTML table from javascript. What we do here is build an HTML
         tree from that javascript, and return that as the HTML of the page. It's very aggressive, but the page is
         very bad.
        """
        csv_lines = []
        for line in text.split('\n'):
            match = re.search('writeListLine\((.*)\);', line)
            if match:
                csv_lines.append(match.group(1))

        # Data is collected. Make pretty XML
        xml_text = '<rows>\n'
        for line in csv_lines:
            values = [value.strip('"') for value in line.split('","')]
            xml_text += '  <row>\n'
            for value in values:
                xml_text += '    <value>%s</value>\n' % value
            xml_text += '  </row>\n'
        xml_text += '</rows>\n'
        return xml_text

    def _get_cookies(self):
        if self.status is None:
            # Run the downloader if it hasn't been run already
            self.html = self._download()
        return self._cookies

    def _get_download_urls(self):
        path = "//value[2]/text()[not(contains(../../value[7]/text(), 'List of Decisions'))]"
        return list('http://2.alalinc.net/library/download/SUPREME/{rel_link}'.format(rel_link=s)
                    for s in self.html.xpath(path))

    def _get_case_names(self):
        def fetcher(html_link):
            full_url = 'http://2.alalinc.net/library/view/file/?lib=SUPREME&file={seed}' % html_link
            logger.info("Running Selenium browser PhantomJS...")
            driver = webdriver.PhantomJS(
                executable_path='/usr/local/phantomjs/phantomjs',
                service_log_path=os.path.devnull,  # Disable ghostdriver.log
            )

            r = requests.get(
                full_url,
                headers={'User-Agent': 'Juriscraper'},
                cookies=self._cookies,
            )
            r.raise_for_status()

            fake_file = StringIO().write(r.text)
            driver.get(fake_file)

            html_tree = html.fromstring(r.text)
            html_tree.make_links_absolute(self.url)
            path =
            description = html_tree.xpath("//text()[contains(., 'Style')]/ancestor::tr[1]/td[2]/text()")[0]


        seed = list(self.html.xpath("//value[2]/text()[not(contains(../../value[7]/text(), 'List of Decisions'))]"))
        return DeferringList(seed=seed, fetcher=fetcher)

    def _get_case_dates(self):
        path = "//value[4]/text()[not(contains(../../value[7]/text(), 'List of Decisions'))]"
        return [datetime.strptime(date_string, '%m/%d/%y').date()
                for date_string in self.html.xpath(path)]

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_names)

    def _get_docket_numbers(self):
        path = "//value[2]/text()[not(contains(../../value[7]/text(), 'List of Decisions'))]"
        return [val.split('.')[0] for val in self.html.xpath(path)]
