"""Scraper for the Maryland Attorney General
CourtID: ag
Court Short Name: Maryland Attorney General
"""

import datetime
from time import sleep
from lxml import html
from selenium.common.exceptions import NoSuchElementException

from juriscraper.OpinionSiteWebDriven import OpinionSiteWebDriven
from juriscraper.lib.string_utils import convert_date_string


class Site(OpinionSiteWebDriven):
    """This scraper is strange. The site it temperamental, and the javascript
    seems to load successfully on some runs, but not on others. The dates are
    also estimated, and the names are actually semi-long summaries. Furthermore,
    the site's source is unmanageable, which has prevented us from being able to
    create legitimate test/example files for coverage. We have a single example
    file that's an empty document skeleton to prevent the test mechanism from
    complaining. But it isn't a test providing real coverage.

    We are doing the best we can with a bad site.
    """

    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.year = datetime.date.today().year
        self.domain = "http://www.marylandattorneygeneral.gov"
        self.url = "%s/Pages/Opinions/index.aspx" % self.domain
        self.back_scrape_iterable = range(1993, self.year + 1)
        self.parent_path_base = '//tbody/tr/td[contains(./text(), "%d")]'
        self.parent_path = self.parent_path_base % self.year
        self.cell_path = '//tbody[@isloaded="true"]/tr/td[%d]'
        self.next_path = '//a[@title="Next"]'

    def _download(self, request_dict={}):
        if self.test_mode_enabled():
            return [super(Site, self)._download(request_dict)]
        trees = self.get_dynamic_html_trees()
        if not len(trees):
            # No opinions for current year on page, SO no
            # js to load.  Return regular page html and
            # extract 0 cases because nothing there
            return [super(Site, self)._download(request_dict)]
        return trees

    def get_dynamic_html_trees(self):
        # Initialize webdriver
        self.initiate_webdriven_session()

        # Find and activate the opinion drop-down for year
        try:
            date_anchor = self.webdriver.find_element_by_xpath(
                "%s/a" % self.parent_path
            )
        except NoSuchElementException:
            # Year has no opinions drop-down on page
            return []
        date_anchor.click()
        trees = [self.get_tree_from_driver_dom()]

        # Handle pagination if more than 30 results for year
        while True:
            try:
                next_anchor = self.webdriver.find_element_by_xpath(
                    self.next_path
                )
            except NoSuchElementException:
                # Less than 30 results
                break
            next_anchor.click()
            trees.append(self.get_tree_from_driver_dom())
        return trees

    def get_tree_from_driver_dom(self):
        # Wait for js to load and dom html to update
        # Seems stupid, but necessary, and easier
        # thank loading lots of selenium dependencies
        # and using complex WebDriverWait with callbacks
        # for attribute to appear, which don't even
        # seem to work consistently with the site's
        # finicky responses.
        sleep(3)
        source = self.webdriver.execute_script(
            "return document.getElementsByTagName('html')[0].innerHTML"
        )
        tree = html.fromstring(source)
        tree.make_links_absolute(self.domain)
        return tree

    def _get_case_names(self):
        names = []
        path = self.cell_path % 3
        for tree in self.html:
            names.extend(
                [cell.text_content().strip() for cell in tree.xpath(path)]
            )
        return names

    def _get_download_urls(self):
        urls = []
        path = (self.cell_path % 4) + "/a/@href"
        for tree in self.html:
            urls.extend([href for href in tree.xpath(path)])
        return urls

    def _get_case_dates(self):
        today = datetime.date.today()
        count = len(self._get_case_names())
        middle_of_year = convert_date_string("July 2, %d" % self.year)
        if self.year == today.year:
            # Not a backscraper, assume cases were filed on day scraped.
            return [today] * count
        else:
            # All we have is the year, so estimate the middle most day
            return [middle_of_year] * count

    def _get_docket_numbers(self):
        dockets = []
        path = self.cell_path % 1
        for tree in self.html:
            for cell in tree.xpath(path):
                dockets.append(cell.text_content().replace("Unpublished", ""))
        return dockets

    def _get_precedential_statuses(self):
        statuses = []
        path = self.cell_path % 1
        for tree in self.html:
            for cell in tree.xpath(path):
                if "Unpublished" in cell.text_content():
                    statuses.append("Unpublished")
                else:
                    statuses.append("Published")
        return statuses

    def _get_date_filed_is_approximate(self):
        return ["True"] * len(self.case_names)

    def _download_backwards(self, year):
        """Iterate over drop down for each year on the page"""
        self.year = year
        self.parent_path = self.parent_path_base % year
        self.html = self._download()
