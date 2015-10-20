# Author: Michael Lissner
# History:
# - 2013-06-11: Birth.
# - 2013-08-06: Revised by Brian Carver
# - 2014-08-05: Updated URL by mlr
from datetime import datetime

import os
import re
from juriscraper.AbstractSite import logger
from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.string_utils import titlecase
from lxml import html
from selenium import webdriver


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = 'http://ujs.sd.gov/Supreme_Court/opinions.aspx'
        self.back_scrape_iterable = [
            (0, 2014),
            (1, 2014),
            (2, 2014),
            (3, 2014),
            (0, 2013),
            (1, 2013),
            (2, 2013),
            (3, 2013),
            (4, 2013),
            (5, 2013),
            (6, 2013),
        ]
        self.uses_selenium = True

    def _get_download_urls(self):
        path = "//table[@id = 'ContentPlaceHolder1_PageContent_gvOpinions']//a/@href[contains(.,'pdf')]"
        return list(self.html.xpath(path))

    def _get_case_names(self):
        path = "//table[@id = 'ContentPlaceHolder1_PageContent_gvOpinions']//tr[position() > 1]/td/a[contains(@href, 'pdf')]/text()"
        case_names = []
        for s in self.html.xpath(path):
            case_name = re.search('(.*)(\d{4} S\.?D\.? \d{1,4})', s, re.MULTILINE).group(1)
            case_names.append(titlecase(case_name.upper()))
        return case_names

    def _get_case_dates(self):
        path = "//table[@id = 'ContentPlaceHolder1_PageContent_gvOpinions']//tr[position() >1]/td[1]/text()"
        return [datetime.strptime(date_string, '%m/%d/%Y').date()
                for date_string in self.html.xpath(path)]

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_names)

    def _get_neutral_citations(self):
        path = "//table[@id = 'ContentPlaceHolder1_PageContent_gvOpinions']//tr[position() > 1]/td/a[contains(@href, 'pdf')]/text()"
        neutral_cites = []
        for s in self.html.xpath(path):
            neutral_cite = re.search('(.*)(\d{4} S\.?D\.? \d{1,4})', s, re.MULTILINE).group(2)
            # Make the citation SD instead of S.D. The former is a neutral cite, the latter, the South Dakota Reporter
            neutral_cites.append(neutral_cite.replace('.', ''))
        return neutral_cites

    def _download_backwards(self, page_year):
        logger.info("Running PhantomJS with params: %s" % (page_year,))
        driver = webdriver.PhantomJS(
            executable_path='/usr/local/phantomjs/phantomjs',
            service_log_path=os.path.devnull,  # Disable ghostdriver.log
        )
        driver.implicitly_wait(30)
        driver.get(self.url)

        # Select the year (this won't trigger a GET unless it's changed)
        path = "//*[@id='ContentPlaceHolder1_PageContent_OpinionYears']/option[@value={year}]".format(year=page_year[1])
        option = driver.find_element_by_xpath(path)
        option.click()

        if page_year[0] != 0:
            # Not the first, page, go to the one desired.
            links = driver.find_elements_by_xpath("//a[@href[contains(., 'Page')]]")
            links[page_year[0] - 1].click()

        text = self._clean_text(driver.page_source)
        driver.quit()
        html_tree = html.fromstring(text)

        html_tree.rewrite_links(self._link_repl)
        self.html = html_tree
        self.status = 200


