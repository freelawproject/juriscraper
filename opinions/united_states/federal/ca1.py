import re
import requests
import time
from datetime import date
from lxml import html
from UserDict import UserDict

class Site(UserDict):
    def __init__(self):
        ''' contains xpath expressions for all meta data'''
        UserDict.__init__(self)
        self['urls'] = ('http://www.ca1.uscourts.gov/opinions/opinionrss.php',)


    def _get_download_links(self):
        return [html.tostring(e, method='text') for e in self['html'].xpath('//item/link')]

    def _get_case_names(self):
        regex = re.compile("(\d{2}-.*?\W)(.*)$")
        return [regex.search(html.tostring(e, method='text')).group(2)
                                  for e in self['html'].xpath('//item/title')]

    def _get_case_dates(self):
        dates = []
        for e in self['html'].xpath('//item/pubdate'):
            date_string = html.tostring(e, method='text').split()[0]
            dates.append(date.fromtimestamp(time.mktime(time.strptime(date_string, '%Y-%m-%d'))))
        return dates

    def _get_docket_numbers(self):
        regex = re.compile("(\d{2}-.*?\W)(.*)$")
        return [regex.search(html.tostring(e, method='text')).group(1)
                                  for e in self['html'].xpath('//item/title')]

    def _get_neutral_citations(self):
        pass

    def _get_precedential_statuses(self):
        statuses = []
        for e in self['html'].xpath("//item/category"):
            text = html.tostring(e, method='text').lower().strip()
            if "unpublished" in text:
                statuses.append("Unpublished")
            elif "published" in text:
                statuses.append("Published")
            elif "errata" in text:
                statuses.append("Errata")
            else:
                statuses.append("Unknown")
        return statuses


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

    def parse(self):
        if self.get('status') != 200:
            # Run the downloader if it hasn't been run already
            self.download_latest()
        self['download_links'] = self._get_download_links()
        self['case_names'] = self._get_case_names()
        self['case_dates'] = self._get_case_dates()
        self['docket_numbers'] = self._get_docket_numbers()
        self['neutral_citations'] = self._get_neutral_citations()
        self['precedential_statuses'] = self._get_precedential_statuses()
        self._post_clean()
        return self

    def _post_clean(self):
        '''TODO: Iterate over all attribute values and clean them'''
        pass

    def download_latest(self):
        # methods for downloading the latest version of Site
        for url in self['urls']:
            # Get the response. Disallow redirects so they throw an error
            r = requests.get(url, allow_redirects=False)

            # Throw an error if a bad status code is returned.
            self['status'] = r.status_code
            r.raise_for_status()

            # Provide the headers to the caller
            self['headers'] = r.headers

            # And finally, get grab the content
            text = self._text_clean(r.content)
            html_tree = html.fromstring(text)
            html_tree.make_links_absolute(url)
            self['html'] = self._pre_clean(html_tree)


    def download_backwards(self):
        # generally recursive methods for the entire Site
        pass
