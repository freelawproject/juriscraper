import certifi
import requests
from juriscraper.AbstractSite import logger
from lxml.html import html5parser, fromstring, tostring

import ca11_p


class Site(ca11_p.Site):
    def __init__(self):
        super(Site, self).__init__()
        self.url = 'http://media.ca11.uscourts.gov/opinions/unpub/logname.php'
        self.court_id = self.__module__
        self.back_scrape_iterable = xrange(20, 22000, 20)

    def _backscrape_download_html5_parser(self, request_dict={}):
        """Replaces the normal download method with one that uses the
        html5parser instead of the normal html parser in lxml. This parser
        should be more forgiving on some of the more terrible pages we've run
        into.

        This is mostly a copy of the _download() method, but with some minor
        tweaks.
        """
        logger.info("Now downloading case page at: %s" % self.url)

        # Set up verify here and remove it from request_dict so you don't send
        # it to s.get or s.post in two kwargs.
        if request_dict.get('verify') is not None:
            verify = request_dict['verify']
            del request_dict['verify']
        else:
            verify = certifi.where()

        s = requests.session()
        r = s.get(
            self.url,
            headers={'User-Agent': 'Juriscraper'},
            verify=verify,
            **request_dict
        )

        # Throw an error if a bad status code is returned.
        r.raise_for_status()

        # Tweak or set the encoding if needed
        r = self._set_encoding(r)

        # Provide the response in the Site object
        self.r = r
        self.status = r.status_code

        # Grab the content. This dance is slightly different than usual because
        # it uses the html5parser to first create an _Element object, then
        # serialize it using `tostring`, then parse *that* using the usual
        # fromstring function. The end result is that irregularities in the html
        # are fixed by the html5parser, and the usual lxml parser gives us the
        # same API wer are used to.
        text = self._clean_text(r.text)
        e = html5parser.document_fromstring(text)
        html_tree = fromstring(tostring(e))
        html_tree.rewrite_links(self._link_repl)
        return html_tree

    def _download_backwards(self, n):
        self.url = 'http://media.ca11.uscourts.gov/opinions/unpub/logname.php?begin={}&num={}&numBegin=1'.format(
            n,
            n/20 - 1
        )

        self.html = self._backscrape_download_html5_parser()
        if self.html is not None:
            # Setting status is important because it prevents the download
            # function from being run a second time by the parse method.
            self.status = 200
