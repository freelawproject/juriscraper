import hashlib
import lxml
import logging.handlers
import re
import requests

from lib.string_utils import clean_string, harmonize

LOG_FILENAME = '/var/log/juriscraper/debug.log'

# Set up a specific logger with our desired output level
logging.basicConfig(format='%(asctime)s %(message)s')
logger = logging.getLogger('Logger')
logger.setLevel(logging.DEBUG)

# Add the log message handler to the logger
handler = logging.handlers.RotatingFileHandler(
              LOG_FILENAME, maxBytes=5120000, backupCount=1)
logger.addHandler(handler)

class InsanityException(Exception):
    def __init__(self, message):
        Exception.__init__(self, message)


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
        self.lower_courts = None

    def __str__(self):
        out = []
        for attr, val in self.__dict__.iteritems():
            out.append('%s: %s' % (attr, val))
        return '\n'.join(out)

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
        self.lower_courts = self._get_lower_courts()
        self._clean_attributes()
        self._check_sanity()
        return self

    def _clean_text(self, text):
        # this function provides the opportunity to clean text before it's made
        # into an HTML tree.
        text = re.sub(r'<!\[CDATA\[', '', text)
        text = re.sub(r'\]\]>', '', text)
        return text

    def _clean_tree(self, html_tree):
        '''Any cleanup code that is needed for the court lives here, for example
        in the case of ca1, we need to flip the sort order of the item elements.
        '''
        return html_tree

    def _clean_attributes(self):
        '''Iterate over attribute values and clean them'''
        self.case_names = [harmonize(clean_string(case_name)) for case_name in self.case_names]

    def _check_sanity(self):
        '''Check that the objects attributes make sense:
        1. Do all the attributes have the same length?
        2. ?
        
        If sanity is OK, no return value. If not, throw InsanityException  
        '''
        lengths = []
        for item in [self.download_links, self.case_names, self.case_dates,
                     self.docket_numbers, self.neutral_citations,
                     self.precedential_statuses, self.lower_courts]:
            if item is not None:
                lengths.append(len(item))
        if lengths.count(lengths[0]) != len(lengths):
            # Are all elements equal?
            raise InsanityException("%s: Scraped meta data fields have unequal lengths: %s"
                                    % (self.court_id, lengths))

    def _download_latest(self):
        # methods for downloading the latest version of Site
        logger.debug("Now scraping: %s" % self.url)
        # Get the response. Disallow redirects so they throw an error
        r = requests.get(self.url, allow_redirects=False,
                         headers={'User-Agent':'Juriscraper'})

        # Throw an error if a bad status code is returned.
        self.status = r.status_code
        r.raise_for_status()

        # Provide the headers to the caller
        self.headers = r.headers

        # Grab the content
        text = self._clean_text(r.content)
        html_tree = lxml.html.fromstring(text)
        html_tree.make_links_absolute(self.url)
        def remove_anchors(href):
            # Some courts have anchors on their links that must be stripped.
            return href.split('#')[0]
        html_tree.rewrite_links(remove_anchors)
        cleaned_tree = self._clean_tree(html_tree)

        # Make a unique ID. Use ETag, Date Modified or make a hash
        if self.headers.get('etag'):
            self.hash = self.headers.get('ETag')
        elif self.headers.get('last-modified'):
            self.hash = self.headers.get('Last-Modified')
        else:
            self.hash = hashlib.sha1(text).hexdigest()

        return cleaned_tree

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

    def _get_lower_courts(self):
        return None


