from lxml.html import html5parser, fromstring, tostring

import ca11_p


class Site(ca11_p.Site):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.url = 'http://media.ca11.uscourts.gov/opinions/unpub/logname.php'
        self.court_id = self.__module__
        self.back_scrape_iterable = xrange(20, 22000, 20)

    def _make_html_tree(self, text):
        """ Grab the content using the html5parser.

        This dance is slightly different than usual because it uses the
        html5parser to first create an _Element object, then serialize it using
        `tostring`, then parse *that* using the usual fromstring function. The
        end result is that irregularities in the html are fixed by the
        html5parser, and the usual lxml parser gives us the same API we are
        used to.

        :param text: The html of the document
        :return: an lxml.HtmlElement object
        """
        e = html5parser.document_fromstring(text)
        html_tree = fromstring(tostring(e))
        return html_tree

    def _download_backwards(self, n):
        self.url = 'http://media.ca11.uscourts.gov/opinions/unpub/logname.php?begin={}&num={}&numBegin=1'.format(
            n,
            n/20 - 1
        )

        self.html = self._download()
        if self.html is not None:
            # Setting status is important because it prevents the download
            # function from being run a second time by the parse method.
            self.status = 200
