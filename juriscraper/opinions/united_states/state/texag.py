"""Scraper for the Texas Attorney General
CourtID: texag
Court Short Name: Texas Attorney General
"""

from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.exceptions import InsanityException
from juriscraper.lib.string_utils import convert_date_string

## WARNING: THIS SCRAPER IS FAILING:
## The page on which the hosting court was
## previously publishing opionions publically
## not shows a messgae that opinions are only
## available upon request. Unless we can convince
## the court to start publishing opinions publicly
## agian, we can get rid of this scraper.


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.target_index = 2
        self.url_path = False
        self.opinion_path = False
        self.section_path = False
        self.year_sub_path = False
        self.opinion_sub_path = False
        self.domain = 'https://texasattorneygeneral.gov'
        self.url = '%s/opinion/index-to-opinions' % self.domain
        self.back_scrape_iterable = range(2, 16)  # Hard coded for initial run
        self.select_sub_path = './/select/option[position()>1]'
        self.flat_list_path = '//a[contains(./text(), "See a flat listing of all opinions")]'
        self.target_sub_page_path_base = '//table/tbody/tr[%d]/td[2]//a/@href'
        self.target_sub_page_path = self.target_sub_page_path_base % self.target_index

    def _download(self, request_dict={}):
        """Follow top-most opinions urls on landing page to resource page"""
        # Process landing page
        landing_html = super(Site, self)._download(request_dict)
        if self.method == 'LOCAL':
            # Example file should be direct resource page
            return landing_html
        # Load resource page
        url = landing_html.xpath(self.target_sub_page_path)[0]
        resource_page_html = self._get_html_tree_by_url(url, request_dict)
        flat_list_link = resource_page_html.xpath(self.flat_list_path)
        if not flat_list_link:
            return resource_page_html
        # Load flat list page for older pages with bad js
        url = flat_list_link[0].xpath('./@href')[0]
        return self._get_html_tree_by_url(url)

    def _get_case_dates(self):
        """All we have are years, so estimate middle most day of year"""
        self.set_dynamic_resource_paths()
        dates = []
        for section in self.html.xpath(self.section_path):
            year = section.xpath(self.year_sub_path)[0].text_content().strip()
            date = convert_date_string('July 2, %s' % year)
            count = len(section.xpath(self.opinion_sub_path))
            dates.extend([date] * count)
        return dates

    def _get_case_names(self):
        """No case names available"""
        return ["Untitled Texas Attorney General Opinion"] * len(self.case_dates)

    def _get_download_urls(self):
        # Some listings provide direct links, others are relative
        return [self.domain + v if self.domain not in v else v
                for v in self.html.xpath(self.url_path)]

    def _get_docket_numbers(self):
        return [option.text_content().strip() for option in self.html.xpath(self.opinion_path)]

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_dates)

    def _get_judges(self):
        breadcrumb = self.html.xpath('//div[contains(@class, "breadcrumb")]//li')[-1].text_content().strip()
        return [breadcrumb.split('Opinions')[0]] * len(self.case_dates)

    def _get_date_filed_is_approximate(self):
        return [True] * len(self.case_dates)

    def _download_backwards(self, index):
        self.target_index = index
        self.target_sub_page_path = self.target_sub_page_path_base % index
        self.html = self._download()

    # Across the whole history of the opinions, the court
    # has used various slightly different page html formats
    # The functions below are used to detect which format
    # the page is using, and set the path variables accordingly.

    def set_dynamic_resource_paths(self):
        self.opinion_path = self.return_opinion_path()
        self.opinion_sub_path = '.%s' % self.opinion_path
        self.url_path = self.return_url_path()
        self.section_path = self.return_section_path()
        self.year_sub_path = self.return_year_sub_path()

    def return_section_path(self):
        paths = [
            '//div[contains(@class, "panel-default")]',
            '//td[contains(p/@class, "center")]',
            '//td[contains(p/@align, "center")]',
            '//td[contains(h2/@class, "center")]',
            '//div[contains(h3/@class, "center")]',
            '//div[contains(h3/@align, "center")]',
        ]
        for path in paths:
            if self.html.xpath(path):
                return path
        raise InsanityException('No recognized path to opinion sections')

    def return_year_sub_path(self):
        parent = self.html.xpath(self.section_path)[0]
        paths = [
            './div[contains(@class, "panel-heading")]/label',
            './p[contains(@class, "center")]/strong',
            './p[contains(@align, "center")]/font/b',
            './h2[contains(@class, "center")]',
            './h3[contains(@class, "center")]',
            './h3[contains(@align, "center")]',
        ]
        for path in paths:
            if parent.xpath(path):
                return path
        raise InsanityException('No recognized path to year string')

    def return_opinion_path(self):
        paths = [
            '//select/option[contains(@value, ".pdf")]',
            '//ul/li/a[contains(@href, ".pdf")]',
        ]
        for path in paths:
            if self.html.xpath(path):
                return path
        raise InsanityException('No recognized path to opinion listings')

    def return_url_path(self):
        if '/option' in self.opinion_path:
            return '%s/@value' % self.opinion_path
        elif '/li/a' in self.opinion_path:
            return '%s/@href' % self.opinion_path
        raise InsanityException('No recognized path to url')
