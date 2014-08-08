"""Scraper for Alabama Supreme Court
CourtID: ala
Court Short Name: Ala. Sup. Ct.
Author: mlr
Reviewer: None
Date created: 2014-07-18

This is one of the most ridiculous scrapers of them all. The list of unusual
hacks includes:

1. We use the _download() method to log into the website and collect cookies
   that we later use for all requests.
2. The page with the content we want contains a beautiful table, but that table
   is generated using JavaScript from values that are in the JavaScript itself.
   We work around this in the _clean_text() method by parsing out the
   JavaScript lines and making them into a nice XML tree.
3. The root page contains Lists of Decisions in addition to actual opinions.
   They're easy to find, but the casing of the text is inconsistent (sometimes
   upper, sometimes lower, etc.) so we lowercase the case names (this doesn't
   affect the final results because we eventually get results from the linked
   pages).
4. Unfortunately, the values on the root page are incomplete, and the next page
   is also formed by executing JavaScript. We work around this by actually
   executing the JavaScript inside PhantomJS, then grabbing the content we
   want.
5. Once we have that content, we have to clean it up because it has more
   information than we need. We do this with a few string manipulation hacks
   in the inner function named fetcher().

What a fragile mess.

The login to alalinc.net is set up by the Alabama Administrative Office of the
Courts. The person to call about it is Myra Sabel. She's very helpful and her
number is 334-229-0580.

"""
from juriscraper.DeferringList import DeferringList
import os
import re

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
            data={'uid': 'juriscraper', 'pwd': 'freelaw'},
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
                if 'list' in value.lower():
                    # A sad hack that's needed because XPath 1.0 doesn't support lower-casing.
                    value = value.lower()
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
        path = "//value[2]/text()[not(contains(../../value[7]/text(), 'list of decisions'))]"
        return list('http://2.alalinc.net/library/download/SUPREME/{rel_link}'.format(rel_link=s)
                    for s in self.html.xpath(path))

    def _get_case_names(self):
        """The case names on the main page only show the first half of long case names. As a result, we browse to the
        pages they link to and compile those pages using Selenium and PhantomJS. Normally we wouldn't do the compilation
        step, but, alas, these pages put all their data into JavaScript functions, where are then executed to create the
        page.

        A couple other notes:
         1. When developing, if you stop this after dirver.get(), you can get the content of the page by doing this:
            https://stackoverflow.com/questions/22739514
        """
        def fetcher(html_link):
            full_url = 'http://2.alalinc.net/library/view/file/?lib=SUPREME&file={seed}'.format(seed=html_link)
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

            # Create a fake HTML page from r.text that can be requested by selenium.
            # See: https://stackoverflow.com/questions/24834838/
            driver.get('data:text/html,' + r.text)
            case_name = driver.find_element_by_xpath("//table[contains(descendant::text(), 'Description')]//tr[2]").text
            case_name = ' '.join(case_name.split())
            case_name = case_name.split('(')[0]
            case_name = case_name.split('PETITION')[0]

            return case_name

        seed = list(self.html.xpath("//value[2]/text()[not(contains(../../value[7]/text(), 'list of decisions'))]"))
        logger.info("Getting {count} pages and rendering them using Selenium browser PhantomJS...".format(count=len(seed)))
        return DeferringList(seed=seed, fetcher=fetcher)

    def _get_case_dates(self):
        path = "//value[4]/text()[not(contains(../../value[7]/text(), 'list of decisions'))]"
        return [datetime.strptime(date_string, '%m/%d/%y').date()
                for date_string in self.html.xpath(path)]

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_names)

    def _get_docket_numbers(self):
        path = "//value[2]/text()[not(contains(../../value[7]/text(), 'list of decisions'))]"
        return [val.split('.')[0] for val in self.html.xpath(path)]
