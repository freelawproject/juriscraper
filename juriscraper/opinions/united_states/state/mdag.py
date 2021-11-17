"""Scraper for the Maryland Attorney General
CourtID: ag
Court Short Name: Maryland Attorney General
"""

from datetime import date
from time import sleep

from lxml import html
from selenium.common.exceptions import NoSuchElementException

from juriscraper.lib.string_utils import convert_date_string
from juriscraper.OpinionSiteWebDriven import OpinionSiteWebDriven


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
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self._set_date_properties()
        self.domain = "http://www.marylandattorneygeneral.gov"
        self.url = f"{self.domain}/Pages/Opinions/index.aspx"
        self.back_scrape_iterable = list(range(1993, self.year + 1))
        self.parent_path_base = '//tbody/tr/td[contains(./text(), "%d")]'
        self.parent_path = self.parent_path_base % self.year
        self.cell_path = '//tbody[@isloaded="true"]/tr/td[%d]'
        self.next_path = '//a[@title="Next"]'

    def _download(self, request_dict={}) -> list:
        if self.test_mode_enabled():
            # NOTE: all test compare files will use this
            # hard-coded date, since the live scraper uses
            # a dynamic date for discovered opinions.
            self._set_date_properties("November 11 2020")
        else:
            trees = self.get_dynamic_html_trees()
        if self.test_mode_enabled() or not len(trees):
            # If not test mode, there arent any opinions for
            # current year on page, SO no js to load. Return
            # regular page html and extract 0 cases because
            # nothing there
            return [super()._download(request_dict)]
        return trees

    def _download_backwards(self, year) -> None:
        """Iterate over drop down for each year on the page"""
        self.year = year
        self.parent_path = self.parent_path_base % year
        self.html = self._download()

    def _get_case_dates(self) -> list:
        """This site doesn't provide actual published dates, so we
        have this system (below) for determining which date to use.
        """
        count = len(self._get_case_names())
        middle_of_year = convert_date_string("July 2, %d" % self.year)
        if self.year == self.today.year:
            # Not a backscraper, assume cases were filed on day scraped.
            return [self.today] * count
        else:
            # All we have is the year, so estimate the middle most day
            return [middle_of_year] * count

    def _get_case_names(self) -> list:
        names = []
        path = self.cell_path % 3
        for tree in self.html:
            names.extend(
                [cell.text_content().strip() for cell in tree.xpath(path)]
            )
        return names

    def _get_date_filed_is_approximate(self) -> list:
        return ["True"] * len(self.case_names)

    def _get_docket_numbers(self) -> list:
        dockets = []
        path = self.cell_path % 1
        for tree in self.html:
            for cell in tree.xpath(path):
                dockets.append(cell.text_content().replace("Unpublished", ""))
        return dockets

    def _get_download_urls(self) -> list:
        urls = []
        path = f"{self.cell_path % 4}/a/@href"
        for tree in self.html:
            urls.extend([href for href in tree.xpath(path)])
        return urls

    def _get_precedential_statuses(self) -> list:
        statuses = []
        path = self.cell_path % 1
        for tree in self.html:
            for cell in tree.xpath(path):
                if "Unpublished" in cell.text_content():
                    statuses.append("Unpublished")
                else:
                    statuses.append("Published")
        return statuses

    def _set_date_properties(self, today: str = None) -> None:
        """Pass in artificial 'today' option for testing only."""
        self.today = convert_date_string(today) if today else date.today()
        self.year = self.today.year

    def get_dynamic_html_trees(self) -> list:
        self.initiate_webdriven_session()

        # Find and activate the opinion drop-down for year
        try:
            path = f"{self.parent_path}/a"
            date_anchor = self.find_element_by_xpath(path)
        except NoSuchElementException:
            # Year has no opinions drop-down on page
            return []

        # if subscription overlay dialog div is present,
        # close it, we will not be subscribing :)
        path_dialog = "//*[@title='Close subscription dialog']"
        dialog = self.find_element_by_xpath(path_dialog)
        if dialog:
            dialog.click()

        # click the appropriate date anchor
        date_anchor.click()

        trees = [self.get_tree_from_driver_dom()]

        # Handle pagination if more than 30 results for year
        while True:
            try:
                next_anchor = self.find_element_by_xpath(self.next_path)
            except NoSuchElementException:
                # Less than 30 results
                break
            next_anchor.click()
            trees.append(self.get_tree_from_driver_dom())
        return trees

    def get_tree_from_driver_dom(self) -> list:
        # Wait for js to load and dom html to update
        # Seems stupid, but necessary, and easier
        # thank loading lots of selenium dependencies
        # and using complex WebDriverWait with callbacks
        # for attribute to appear, which don't even
        # seem to work consistently with the site's
        # finicky responses.
        sleep(3)
        script = "return document.getElementsByTagName('html')[0].innerHTML"
        source = self.webdriver.execute_script(script)
        tree = html.fromstring(source)
        tree.make_links_absolute(self.domain)
        return tree
