# Scraper for New York Appellate Divisions 4th Dept.
#CourtID: nyappdiv_4th
#Court Short Name: NY
#Author: Andrei Chelaru
#Reviewer: mlr
#Date: 2014-07-04

from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.string_utils import convert_date_string


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.back_scrape_iterable = ['']
        self.backscraping = False
        self.path_to_year_links = '//div[@id="editBody"]/table/tr[2]/td/a[1]/@href'
        self.path_to_date_links = '//ul[@class="nav nav-pills nav-stacked"]/li/a[1]/@href'
        self.path_to_cases_link = '//a[contains(text(), "- by CASE NAME")]/@href[1]'
        self.path_to_date = '//div[@class="page-header"]/h1/small'
        self.path_to_row = '//div[@id="editBody"]//tr'
        self.url = "http://www.nycourts.gov/courts/ad4/Clerk/Decisions/"
        self.cases = []

    def _download(self, request_dict={}):
        """Traverse link tree to find pertinent resource pages.

        This is a fun scraper, because we need to traverse multiple
        landing pages in order to find the target resource pages,
        since they are not posted on a regular schedule that would
        allow up to algorithmically build target resource urls.
        """
        landing_page_html = super(Site, self)._download(request_dict)

        # Test files should be direct target resource page html,
        # not landing page. This prevents hitting the network on tests.
        if self.method == 'LOCAL':
            self.extract_case_data_from_html(landing_page_html)
            return landing_page_html

        # For live runs, traverse landing page tree
        html_trees = []
        for year_link in landing_page_html.xpath(self.path_to_year_links):
            years_page_html = self._get_html_tree_by_url(year_link)
            for date_link in years_page_html.xpath(self.path_to_date_links):
                # Stop processing after first resource page if not running backscraper
                if not self.backscraping and html_trees:
                    return html_trees
                # Crappy anchor html practices make below necessary
                if not date_link.endswith('.html') and not date_link.endswith('/'):
                    date_link += '/'
                date_page_html = self._get_html_tree_by_url(date_link)
                cases_link = date_page_html.xpath(self.path_to_cases_link)
                if cases_link:
                    cases_page_html = self._get_html_tree_by_url(cases_link[0])
                    self.extract_case_data_from_html(cases_page_html)
                    html_trees.append(cases_page_html)
        return html_trees

    def _download_backwards(self, _):
        self.backscraping = True
        # Adjust paths to work with legacy pages
        self.path_to_date_links += ' | //div[@id="page_content"]/a/@href[1]'
        self.path_to_row += ' | //div[@id="page_content"]//tr'
        self.path_to_date += ' | //div[@id="page_content"]/p[1]'
        self.html = self._download()

    def extract_case_data_from_html(self, html):
        date_element = html.xpath(self.path_to_date)[0]
        date_string = date_element.text_content().strip().replace('Decisions - ', '')
        date = convert_date_string(date_string)
        for row in html.xpath(self.path_to_row):
            first_cell = row.xpath('./td[1]')
            # Skip blank rows that court sometimes includes
            if first_cell:
                name = first_cell[0].text_content().strip()
                # Skip non case record that court sometimes includes at bottom of table
                if self.is_valid_name(name):
                    self.cases.append({
                        'name': name,
                        'url': row.xpath('./td[1]/a/@href')[0],
                        'docket': row.xpath('./td[3]')[0].text_content().strip(),
                        'date': date,
                        'status': 'Published'
                    })

    def is_valid_name(self, name):
        if not name:
            return False
        lower = name.lower()
        if 'motions' in lower and 'crawfords' in lower:
            return False
        if lower == 'motions':
            return False
        return True

    def _get_case_dates(self):
        return [case['date'] for case in self.cases]

    def _get_case_names(self):
        return [case['name'] for case in self.cases]

    def _get_download_urls(self):
        return [case['url'] for case in self.cases]

    def _get_precedential_statuses(self):
        return [case['status'] for case in self.cases]

    def _get_docket_numbers(self):
        return [case['docket'] for case in self.cases]
