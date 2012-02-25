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
    scrapers. 
    
    Should not contain lists that can't be sorted by the _date_sort function.'''
    def __init__(self):
        super(GenericSite, self).__init__()
        self.html = None
        self.status = None
        self.method = 'GET'
        self.hash = None
        self.download_links = None
        self.case_names = None
        self.case_dates = None
        self.docket_numbers = None
        self.neutral_citations = None
        self.precedential_statuses = None
        self.lower_courts = None
        self.lower_court_judges = None
        self.dispositions = None
        self.judges = None
        self.nature_of_suit = None

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
        self.lower_court_judges = self._get_lower_court_judges()
        self.dispositions = self._get_dispositions()
        self.judges = self._get_judges()
        self.nature_of_suit = self._get_nature_of_suit()
        self._clean_attributes()
        self._check_sanity()
        self._date_sort()
        self._make_hash()
        return self

    def _clean_text(self, text):
        # this function provides the opportunity to clean text before it's made
        # into an HTML tree.
        text = re.sub(r'<!\[CDATA\[', '', text)
        text = re.sub(r'\]\]>', '', text)
        return text

    def _clean_attributes(self):
        '''Iterate over attribute values and clean them'''
        for item in [self.docket_numbers, self.neutral_citations,
                     self.lower_courts, self.lower_court_judges,
                     self.dispositions, self.judges, self.nature_of_suit]:
            if item is not None:
                item[:] = [clean_string(sub_item) for sub_item in item]
        if self.case_names is not None:
            self.case_names = [harmonize(clean_string(case_name))
                                    for case_name in self.case_names]

    def _check_sanity(self):
        '''Check that the objects attributes make sense:
        1. Do all the attributes have the same length?
        2. ?
        
        If sanity is OK, no return value. If not, throw InsanityException  
        '''
        lengths = []
        for item in [self.download_links, self.case_names, self.case_dates,
                     self.docket_numbers, self.neutral_citations,
                     self.precedential_statuses, self.lower_courts,
                     self.lower_court_judges, self.dispositions,
                     self.judges]:
            if item is not None:
                lengths.append(len(item))
        if lengths.count(lengths[0]) != len(lengths):
            # Are all elements equal?
            raise InsanityException("%s: Scraped meta data fields have unequal lengths: %s"
                                    % (self.court_id, lengths))
        logger.debug("%s: Successfully found %s items." % (self.court_id,
                                                           len(self.case_names)))

    def _date_sort(self):
        ''' This function sorts the object by date. It's a good candidate for
        re-coding due to violating DRY and because it works by checking for 
        lists.
        '''
        # Note that case_dates must be first for sorting to work.
        obj_list_attrs = [item for item in [self.case_dates, self.download_links,
                                            self.case_names, self.docket_numbers,
                                            self.neutral_citations, self.precedential_statuses,
                                            self.lower_courts, self.lower_court_judges,
                                            self.dispositions, self.judges]
                                            if isinstance(item, list)]
        zipped = zip(*obj_list_attrs)
        zipped.sort(reverse=True)
        i = 0
        obj_list_attrs = zip(*zipped)
        for item in [self.case_dates, self.download_links,
                     self.case_names, self.docket_numbers,
                     self.neutral_citations, self.precedential_statuses,
                     self.lower_courts, self.lower_court_judges,
                     self.dispositions, self.judges]:
            if isinstance(item, list):
                item[:] = obj_list_attrs[i][:]
                i += 1

    def _make_hash(self):
        # Make a unique ID. Use ETag, Date Modified or make a hash
        if self.headers.get('etag'):
            self.hash = self.headers.get('ETag')
        elif self.headers.get('last-modified'):
            self.hash = self.headers.get('Last-Modified')
        else:
            self.hash = hashlib.sha1(str(self.case_names)).hexdigest()

    def _download_latest(self):
        # methods for downloading the latest version of Site
        logger.debug("Now scraping: %s" % self.url)
        # Get the response. Disallow redirects so they throw an error
        if self.method == 'GET':
            r = requests.get(self.url, allow_redirects=False,
                             headers={'User-Agent':'Juriscraper'})
        elif self.method == 'POST':
            r = requests.post(self.url, allow_redirects=False,
                             headers={'User-Agent':'Juriscraper'},
                             data=self.parameters)

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

        return html_tree

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

    def _get_lower_court_judges(self):
        return None

    def _get_dispositions(self):
        return None

    def _get_judges(self):
        return None

    def _get_nature_of_suit(self):
        return None

