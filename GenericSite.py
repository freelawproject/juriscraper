import lxml
import requests
from UserDict import UserDict

class GenericSite(object):
    '''Contains generic methods for scraping data. Should be extended by all
    scrapers.'''
    def __init__(self):
        super(GenericSite, self).__init__()
        self.html = self._download_latest()
        self.download_links = self._get_download_links()
        self.case_names = self._get_case_names()
        self.case_dates = self._get_case_dates()
        self.docket_numbers = self._get_docket_numbers()
        self.neutral_citations = self._get_neutral_citations()
        self.precedential_statuses = self._get_precedential_statuses()

    def _get_download_links(self):
        pass

    def _get_case_names(self):
        pass

    def _get_case_dates(self):
        pass

    def _get_docket_numbers(self):
        pass

    def _get_neutral_citations(self):
        pass

    def _get_precedential_statuses(self):
        pass

    def parse(self):
        if self.status != 200:
            # Run the downloader if it hasn't been run already
            self.download_latest()
        self._post_clean()
        return self

    def _post_clean(self):
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
            text = self._text_clean(r.content)
            html_tree = lxml.html.fromstring(text)
            html_tree.make_links_absolute(url)
            html = self._pre_clean(html_tree)
            return html

    def download_backwards(self):
        # generally recursive methods for the entire Site
        pass

