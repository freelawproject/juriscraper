import lxml
import re
import requests

class GenericSite(object):
    '''Contains generic methods for scraping data. Should be extended by all
    scrapers.'''
    def __init__(self):
        super(GenericSite, self).__init__()
        self.html = None
        self.status = None
        self.download_links = None
        self.case_names = None
        self.case_dates = None
        self.docket_numbers = None
        self.neutral_citations = None
        self.precedential_statuses = None

    def parse(self):
        if self.status != 200:
            # Run the downloader if it hasn't been run already
            self.html = self._download_latest()
        self.download_links = self._get_download_links()
        self.case_names = self._get_case_names()
        self.case_dates = self._get_case_dates()
        self.docket_numbers = self._get_docket_numbers()
        self.neutral_citations = self._get_neutral_citations()
        self.precedential_statuses = self._get_precedential_statuses()
        self._clean_attributes()
        return self

    def _clean_text(self, text):
        # this function provides the opportunity to clean text before it's made
        # into an HTML tree.
        text = re.sub(r'<!\[CDATA\[', '', text)
        text = re.sub(r'\]\]>', '', text)
        return text

    def _clean_tree(self, dirty_html):
        '''Any cleanup code that is needed for the court lives here, for example
        in the case of ca1, we need to flip the sort order of the item elements.
        '''
        return dirty_html

    def _clean_attributes(self):
        '''TODO: Iterate over all attribute values and clean them'''
        pass

    def _download_latest(self):
        # methods for downloading the latest version of Site
        for url in self.urls:
            # Get the response. Disallow redirects so they throw an error
            r = requests.get(url, allow_redirects=False)

            # Throw an error if a bad status code is returned.
            self.status = r.status_code
            r.raise_for_status()

            # Provide the headers to the caller
            self.headers = r.headers

            # And finally, grab the content
            text = self._clean_text(r.content)
            html_tree = lxml.html.fromstring(text)
            html_tree.make_links_absolute(url)
            cleaned_html = self._clean_tree(html_tree)
            return cleaned_html

    def _download_backwards(self):
        # generally recursive methods for the entire Site
        pass

    def _get_download_links(self):
        return None

    def _get_case_names(self):
        return None

    def _get_case_dates(self):
        return None

    def _get_docket_numbers(self):
        return None

    def _get_neutral_citations(self):
        return None

    def _get_precedential_statuses(self):
        return None


