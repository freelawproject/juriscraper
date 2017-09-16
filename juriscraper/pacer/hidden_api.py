from lxml import etree

from ..lib.log_tools import make_default_logger
from ..lib.string_utils import force_unicode

logger = make_default_logger()


class PossibleCaseNumberApi(object):
    """Tools for gathering data from the "Possible case numbers" hidden API.

    This API takes a docket number and a court as input, and returns an XML
    object with the pacer_case_id, title, normalized docket number, and a few
    other things.

    This API is normally used via AJAX in the front end of PACER when you put a
    docket number into the docket report search box.
    """
    def __init__(self, pacer_session=None):
        self.session = pacer_session
        self.xml_tree = None
        super(PossibleCaseNumberApi, self).__init__()

    @staticmethod
    def url(court_id):
        if court_id == 'psc':
            return "https://dcecf.psc.uscourts.gov/cgi-bin/possible_case_numbers.pl"
        else:
            return "https://ecf.%s.uscourts.gov/cgi-bin/possible_case_numbers.pl" % court_id

    def query(self, docket_number, court_id):
        """Query the "possible case numbers" endpoint and return the results.

        :param docket_number: A string representing a docket number
        :param court_id: A string representing the court_id of the case
        :return: a request response object
        """
        assert self.session is not None, \
            "session attribute of DocketReport cannot be None."
        url = "%s?%s" % (self.url(court_id), docket_number)
        logger.info(u'Querying the possible case number endpoint at URL: %s' %
                    url)
        return self.session.get(url, timeout=300)

    def parse_text(self, text):
        """Parse the response object and return it as data."""
        self.xml_tree = etree.fromstring(text)

    def parse_response(self, response):
        response.raise_for_status()
        self.parse_text(response.text)

    @property
    def data(self):
        """Get all the data back from this query"""
        try:
            return {
                u'docket_number': force_unicode(
                    self.xml_tree.xpath('//case/@number')[0]
                ),
                u'pacer_case_id': force_unicode(
                    self.xml_tree.xpath('//case/@id')[0]
                ),
                # This could be further post processed to pull out the date closed
                # and a cleaner title.
                u'title': force_unicode(
                    self.xml_tree.xpath('//case/@title')[0]
                ),
            }
        except IndexError:
            msg = self.xml_tree.xpath('//message/@text')[0]
            if "Cannot find case" in msg:
                logger.info("Cannot find case.")
                return None
            else:
                raise Exception("Unknown XML content in PossibleCaseNumberApi "
                                "result.")


