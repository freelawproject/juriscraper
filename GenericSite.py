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

    def parse(self):
        if self.status != 200:
            # Run the downloader if it hasn't been run already
            self._download_latest()
        self._post_clean()
        return self

    def _text_clean(self, text):
        # this function provides the opportunity to clean text before it's made
        # into an HTML tree.
        text = re.sub(r'<!\[CDATA\[', '', text)
        text = re.sub(r'\]\]>', '', text)
        return text

    def _pre_clean(self, dirty_html):
        '''Any cleanup code that is needed for the court lives here, for example
        in the case of ca1, we need to flip the sort order of the item elements.
        '''
        clean_html = dirty_html

        return clean_html
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
            cleaned_html = self._pre_clean(html_tree)
            return cleaned_html

    def download_backwards(self):
        # generally recursive methods for the entire Site
        pass

