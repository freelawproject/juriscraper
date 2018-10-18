"""Scraper for the United States Court of Appeals for the Armed Forces
CourtID: armfor
Court Short Name: C.A.A.F."""

from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.html_utils import get_html5_parsed_text
from juriscraper.lib.string_utils import convert_date_string


# This court has some funky html that varies
# across the old term listings. Before committing
# changes, make sure you haven't broken the backscraper
# by running: python juriscraper/sample_caller.py -c opinions.united_states.federal_special.armfor --backscrape
class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.back_scrape_iterable = ['']
        self.url = "http://www.armfor.uscourts.gov/newcaaf/opinions.htm"
        self.row_base_path = '//table[@border="1"]//tr[descendant::a]'
        self.path_to_landing_page_links = '//blockquote/ul/li[1]/font/a[1]/@href'
        # Site has non-chained, bad certificate, need to
        # ignore ssl verification for now for scraper to work
        self.request['verify'] = False


    def _download(self, request_dict={}):
        landing_page_html = super(Site, self)._download(request_dict)

        # Example test files should include html of direct resource page
        if self.method == 'LOCAL':
            return [landing_page_html]

        urls = landing_page_html.xpath(self.path_to_landing_page_links)
        return [self._get_html_tree_by_url(url, request_dict) for url in urls]

    def _get_case_names(self):
        names = []
        path = '%s/td[1]' % self.row_base_path
        for html_tree in self.html:
            names.extend([cell.text_content().strip() for cell in html_tree.xpath(path)])
        return names

    def _get_download_urls(self):
        urls = []
        path = '%s/td[2]//a[last()]/@href' % self.row_base_path
        for html_tree in self.html:
            urls.extend([url for url in html_tree.xpath(path)])
        return urls

    def _get_case_dates(self):
        dates = []
        path = '%s/td[3]' % self.row_base_path
        for html_tree in self.html:
            for cell in html_tree.xpath(path):
                dates.append(convert_date_string(cell.text_content()))
        return dates

    def _get_docket_numbers(self):
        dockets = []
        path = '%s//td[2]' % self.row_base_path
        for html_tree in self.html:
            for cell in html_tree.xpath(path):
                docket_raw = cell.text_content().strip()
                dockets.append(docket_raw.rstrip('(PDF)'))
        return dockets

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_names)

    def _download_backwards(self, _):
        # We skip the 1998 and 1999 entries because they
        # are formatted differently and don't contain dates
        limitation = 'not(contains(@href, "1998Term.htm")) and not(contains(@href, "1997Term.htm"))'
        self.path_to_landing_page_links = '//blockquote/ul/li/font/a[1][%s]/@href' % limitation
        self.html = self._download()

    def _make_html_tree(self, text):
        return get_html5_parsed_text(text)
