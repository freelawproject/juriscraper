from datetime import date
import hashlib
import logging.handlers
import re
import requests

from lxml import html
from juriscraper.lib.string_utils import harmonize, clean_string, trunc
from juriscraper.tests import MockRequest
from urlparse import urlsplit, urlunsplit, urljoin

LOG_FILENAME = '/var/log/juriscraper/debug.log'

# Set up a specific logger with our desired output level
logger = logging.getLogger('Logger')
logger.setLevel(logging.DEBUG)

# make a formatter
formatter = logging.Formatter('%(asctime)s - %(levelname)s: %(message)s')

# Create a handler, and attach it to the logger
handler = logging.handlers.RotatingFileHandler(LOG_FILENAME,
                                               maxBytes=5120000,
                                               backupCount=7)
logger.addHandler(handler)
handler.setFormatter(formatter)

# logging.basicConfig(format='%(asctime)s - %(levelname)s: %(message)s',
#                    level=logging.DEBUG)


class InsanityException(Exception):
    def __init__(self, message):
        Exception.__init__(self, message)


class AbstractSite(object):
    """Contains generic methods for scraping data. Should be extended by all
    scrapers.

    Should not contain lists that can't be sorted by the _date_sort function."""

    def __init__(self):
        super(AbstractSite, self).__init__()

        # Computed metadata
        self.hash = None
        self.html = None
        self.method = 'GET'
        self.use_sessions = False
        self.status = None
        self.back_scrape_iterable = None
        self._cookies = []

        # Upstream metadata
        self.court_id = None
        self.url = None
        self.parameters = None
        self._opt_attrs = []
        self._req_attrs = []
        self._all_attrs = []

    def __str__(self):
        out = []
        for attr, val in self.__dict__.iteritems():
            out.append('%s: %s' % (attr, val))
        return '\n'.join(out)

    def parse(self):
        if self.status is None:
            # Run the downloader if it hasn't been run already
            self.html = self._download()

        # Set the attribute to the return value from _get_foo()
        # e.g., this does self.case_names = _get_case_names()
        for attr in self._all_attrs:
            self.__setattr__(attr, getattr(self, '_get_%s' % attr)())

        self._clean_attributes()
        self._post_parse()
        self._check_sanity()
        self._date_sort()
        self._make_hash()
        return self

    def tweak_request_object(self, r):
        """
        Does nothing, but provides a hook that allows inheriting objects to
        tweak the requests object if necessary.
        """
        pass

    def _clean_text(self, text):
        """ Cleans up text before we make it into an HTML tree:
            1. Nukes <![CDATA stuff.
            2. Nukes XML encoding declarations
            3. Replaces </br> with <br/>
            4. Nukes invalid bytes in input
            5. ?
        """
        # Remove <![CDATA because it causes breakage in lxml.
        text = re.sub(r'<!\[CDATA\[', '', text)
        text = re.sub(r'\]\]>', '', text)

        # Remove <?xml> declaration in Unicode objects, because it causes an error:
        # "ValueError: Unicode strings with encoding declaration are not supported."
        # Note that the error only occurs if the <?xml> tag has an "encoding"
        # attribute, but we remove it in all cases, as there's no downside to
        # removing it. This moves our encoding detection to chardet, rather than
        # lxml.
        if isinstance(text, unicode):
            text = re.sub(r'^\s*<\?xml\s+.*?\?>', '', text)

        # Fix </br>
        text = re.sub('</br>', '<br/>', text)

        # Fix invalid bytes (http://stackoverflow.com/questions/8733233/filtering-out-certain-bytes-in-python)
        def valid_xml_char_ordinal(c):
            code_point = ord(c)
            # conditions ordered by presumed frequency
            return (
                0x20 <= code_point <= 0xD7FF or
                code_point in (0x9, 0xA, 0xD) or
                0xE000 <= code_point <= 0xFFFD or
                0x10000 <= code_point <= 0x10FFFF
            )
        text = ''.join(c for c in text if valid_xml_char_ordinal(c))

        return text

    def _clean_attributes(self):
        """Iterate over attribute values and clean them"""
        for attr in self._all_attrs:
            item = getattr(self, attr)
            if item is not None:
                cleaned_item = []
                for sub_item in item:
                    if attr == 'download_urls':
                        sub_item = sub_item.strip()
                    else:
                        if isinstance(sub_item, basestring):
                            sub_item = clean_string(sub_item)
                        if attr in ['case_names', 'docket_numbers']:
                            sub_item = harmonize(sub_item)
                    cleaned_item.append(sub_item)
                self.__setattr__(attr, cleaned_item)

    def _post_parse(self):
        """This provides an hook for subclasses to do custom work on the data after the parsing is complete."""
        pass

    def _check_sanity(self):
        """Check that the objects attributes make sense:
            1. Do all the attributes have the same length?
            2. Do we have any content at all?
            3. Is there a bare minimum of meta data?
            4. Are the dates datetime objects, not strings?
            5. Are case_names more than just empty whitespace?
            6. ?

        The signature of this method is subject to change as additional checks become
        convenient.

        Inheriting classes should override this method calling super to give it the
        necessary parameters.

        If sanity is OK, no return value. If not, throw InsanityException or
        warnings, as appropriate.
        """
        lengths = {}
        for attr in self._all_attrs:
            if self.__getattribute__(attr) is not None:
                lengths[attr] = len(self.__getattribute__(attr))
        values = lengths.values()
        if values.count(values[0]) != len(values):
            # Are all elements equal?
            raise InsanityException("%s: Scraped meta data fields have differing"
                                    " lengths: %s" % (self.court_id, lengths))
        if len(self.case_names) == 0:
            logger.warning('%s: Returned with zero items.' % self.court_id)
        else:
            for field in self._req_attrs:
                if self.__getattribute__(field) is None:
                    raise InsanityException('%s: Required fields do not contain any data: %s' % (self.court_id, field))
            i = 0
            for name in self.case_names:
                if not name.strip():
                    raise InsanityException("Item with index %s has an empty case name." % i)
                i += 1

        for d in self.case_dates:
            if not isinstance(d, date):
                raise InsanityException('%s: member of case_dates list not a valid date object. '
                                        'Instead it is: %s with value: %s' % (self.court_id, type(d), d))
        logger.info("%s: Successfully found %s items." % (self.court_id,
                                                          len(self.case_names)))

    def _date_sort(self):
        """ Sort the object by date.
        """
        if len(self.case_names) > 0:
            obj_list_attrs = [self.__getattribute__(attr) for attr in
                              self._all_attrs if
                              isinstance(self.__getattribute__(attr), list)]
            zipped = zip(*obj_list_attrs)
            zipped.sort(reverse=True)
            i = 0
            obj_list_attrs = zip(*zipped)
            for attr in self._all_attrs:
                if isinstance(self.__getattribute__(attr), list):
                    self.__setattr__(attr, obj_list_attrs[i][:])
                    i += 1

    def _make_hash(self):
        """Make a unique ID. ETag and Last-Modified from courts cannot be
        trusted
        """
        self.hash = hashlib.sha1(str(self.case_names)).hexdigest()

    def _link_repl(self, href):
        """Makes links absolute, working around buggy URLs and nuking anchors.

        Some URLS, like the following, make no sense:
         - https://www.appeals2.az.gov/../Decisions/CR20130096OPN.pdf.
                                      ^^^^ -- This makes no sense!
        The fix is to remove any extra '/..' patterns at the beginning of the
        path.

        Others have annoying anchors on the end, like:
         - http://example.com/path/#anchor

        Note that lxml has a method generally for this purpose called
        make_links_absolute, but we cannot use it because it does not work
        around invalid relative URLS, nor remove anchors. This is a limitation
        of Python's urljoin that will be fixed in Python 3.5 according to a bug
        we filed: http://bugs.python.org/issue22118
        """
        url_parts = urlsplit(urljoin(self.url, href))
        url = urlunsplit(
            url_parts[:2] +
            (re.sub('^(/\.\.)+', '', url_parts.path),) +
            url_parts[3:]
        )
        return url.split('#')[0]

    def _download(self, request_dict={}):
        """Methods for downloading the latest version of Site
        """
        if self.method == 'POST':
            truncated_params = {}
            for k, v in self.parameters.iteritems():
                truncated_params[k] = trunc(v, 50, elipsize=True, elipsis='...[truncated]')
            logger.info("Now downloading case page at: %s (params: %s)" % (self.url, truncated_params))
        else:
            logger.info("Now downloading case page at: %s" % self.url)
        # Get the response. Disallow redirects so they throw an error
        s = requests.session()
        if self.method == 'GET':
            r = s.get(self.url,
                      headers={'User-Agent': 'Juriscraper'},
                      **request_dict)
        elif self.method == 'POST':
            r = s.post(self.url,
                       headers={'User-Agent': 'Juriscraper'},
                       data=self.parameters,
                       **request_dict)
        elif self.method == 'LOCAL':
            mr = MockRequest(url=self.url)
            r = mr.get()

        # Provides a hook for inheriting objects to tweak the request object.
        self.tweak_request_object(r)

        # Throw an error if a bad status code is returned.
        r.raise_for_status()

        # If the encoding is iso-8859-1, switch it to cp1252 (a superset)
        if r.encoding == 'ISO-8859-1':
            r.encoding = 'cp1252'

        # Provide the response in the Site object
        self.r = r
        self.status = r.status_code

        # Grab the content
        text = self._clean_text(r.text)
        html_tree = html.fromstring(text)
        html_tree.rewrite_links(self._link_repl)
        return html_tree

    def _download_backwards(self):
        # methods for downloading the entire Site
        pass

    @staticmethod
    def _cleanup_content(content):
        """
          Given the HTML from a page, the binary PDF file, or similar, do any
          last-minute cleaning.

          This method should be called as the last step by any caller and works
          to do any cleanup that is necessary. Usually, this is needed on HTML
          pages, in jurisdictions that post their content in an HTML page with
          headers, footers and other content must be stripped after the page
          has been downloaded by the caller.
        """
        return content

    def _get_cookies(self):
        """
          Some websites require cookies in order to be scraped. This method
          provides a hook where cookies can be retrieved by calling functions.
          Generally the cookies will be set by the _download() method.

          self.cookies is a list of dicts of the form:
          [
              {
                  u'domain':   u'www.search.txcourts.gov',
                  u'httponly': True,
                  u'name':     u'ASP.NET_SessionId',
                  u'path':     u'/',
                  u'secure':   False,
                  u'value':    u'hryku05534xhgr45yxvusuux'
              },
          ]
        """
        return self._cookies
