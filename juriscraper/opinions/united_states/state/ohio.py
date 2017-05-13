"""Scraper for the Supreme Court of Ohio
CourtID: ohio
Court Short Name: Ohio
Author: Andrei Chelaru
Reviewer: mlr
History:
 - Stubbed out by Brian Carver
 - 2014-07-30: Finished by Andrei Chelaru
 - 2015-07-31: Redone by mlr to use ghost driver. Alas, their site used to be
               great, but now it's terribly frustrating.
"""
from datetime import date, datetime

import os
from juriscraper.AbstractSite import logger
from juriscraper.OpinionSite import OpinionSite
from lxml import html
from lxml.html import tostring
from selenium import webdriver

from juriscraper.lib.html_utils import fix_links_in_lxml_tree
from juriscraper.lib.string_utils import clean_if_py3


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        # Changing the page # in the url will get additional pages
        # Changing the source # (0-13) will get the 12 Courts of Appeals and
        # the Court of Claims. We do not use the "all sources" link because a
        # single day might yield more than 25 opinions and this scraper is
        # not designed to walk through multiple pages.
        self.court_index = 0
        self.year = str(date.today().year)
        self.url = 'http://www.supremecourtofohio.gov/rod/docs/'
        self.court_id = self.__module__
        self.base_path = "id('MainContent_gvResults')//tr[position() > 1]/td[2][string-length(normalize-space(text())) > 1]"
        self.uses_selenium = True

    def _download(self, request_dict={}):
        """This is another of the cursed MS asp.net pages with damned POST
          parameters like __EVENTVALIDATION. These are near impossible to
          scrape without using Selenium.
        """
        if self.method == 'LOCAL':
            return super(Site, self)._download(request_dict=request_dict)
        else:
            driver = webdriver.PhantomJS(
                executable_path='/usr/local/phantomjs/phantomjs',
                service_log_path=os.path.devnull,  # Disable ghostdriver.log
            )
            driver.implicitly_wait(30)
            logger.info("Now downloading case page at: %s" % self.url)
            driver.get(self.url)

            # Court drop down...
            driver.find_element_by_xpath(
                "//select[@id='MainContent_ddlCourt']"
                "/option[@value='{court}']".format(court=self.court_index)
            ).click()

            # Year drop down...
            yearDropDownId = 'MainContent_ddlDecidedYear'
            yearDropDownPath = "//select[@id='{id}']/option[@value='%s']" % self.year
            yearDropdownPaths = [
                yearDropDownPath.format(id=yearDropDownId),             # Legacy examples
                yearDropDownPath.format(id=yearDropDownId + 'Min'),     # current (2017)
            ]
            driver.find_element_by_xpath(' | '.join(yearDropdownPaths)).click()

            # Hit submit
            submitPath = "//input[@id='MainContent_btnSubmit']"
            driver.find_element_by_xpath(submitPath).click()

            # Selenium doesn't give us the actual code, we have to hope.
            self.status = 200

            text = self._clean_text(driver.page_source)
            html_tree = html.fromstring(text)
            html_tree.rewrite_links(fix_links_in_lxml_tree,
                                    base_href=self.request['url'])
        return html_tree

    def _get_case_names(self):
        path = "{base}/preceding::td[1]".format(base=self.base_path)
        case_names = []
        for e in self.html.xpath(path):
            case_names.append(
                tostring(e, method='text', encoding='unicode').strip()
            )
        return case_names

    def _get_download_urls(self):
        path = "{base}/preceding::td[1]//a[1]/@href".format(base=self.base_path)
        return list(self.html.xpath(path))

    def _get_docket_numbers(self):
        path = "{base}//text()".format(base=self.base_path)
        return list(self.html.xpath(path))

    def _get_summaries(self):
        path = "{base}/following::td[1]//text()".format(base=self.base_path)
        return list(self.html.xpath(path))

    def _get_case_dates(self):
        path = "{base}/following::td[4]//text()".format(base=self.base_path)
        dates = []
        for s in self.html.xpath(path):
            dates.append(datetime.strptime(clean_if_py3(s).strip(), '%m/%d/%Y').date())
        return dates

    def _get_neutral_citations(self):
        path = "{base}/following::td[6]//text()".format(base=self.base_path)
        return [s.replace('-', ' ') for s in self.html.xpath(path)]

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_names)

    def _get_judges(self):
        path = "{base}/following::td[2]".format(base=self.base_path)
        return map(self._return_judge, self.html.xpath(path))

    @staticmethod
    def _return_judge(e):
        txt = e.xpath(".//text()")
        if txt:
            return txt[0]
        else:
            return ''
