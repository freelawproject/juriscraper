from lxml import etree

from ..lib.diff_tools import get_closest_match_index
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
        :param court_id: A string representing the pacer court_id of the case
        :return: a request response object
        """
        assert self.session is not None, \
            "session attribute of DocketReport cannot be None."
        url = "%s?%s" % (self.url(court_id), docket_number)
        logger.info(u'Querying the possible case number endpoint at URL: %s' %
                    url)
        return self.session.get(url, timeout=300)

    def parse_text(self, text):
        """Parse the text of the response object and put it in the xml_tree attribute.
        """
        self.xml_tree = etree.fromstring(text)

    def parse_response(self, response):
        response.raise_for_status()
        self.parse_text(response.text)

    def data(self, case_name=None):
        """Get data back from this query for the matching case.

        :param case_name: This endpoint can return multiple cases for a given
        query. If a case name is provided, and more than one case is returned,
        we will try to identify the most similar case.
        """
        case_count = self.xml_tree.xpath('count(//case)')
        if case_count == 0:
            try:
                msg = self.xml_tree.xpath('//message/@text')[0]
            except IndexError:
                pass
            else:
                if "Cannot find case" in msg:
                    logger.info("Cannot find case.")
                    return None
            raise Exception("Unknown XML content in PossibleCaseNumberApi "
                            "result.")
        elif case_count == 1:
            case_index = 0
        elif case_count > 1:
            if case_name is not None:
                # Disambiguate the possible case nodes to find the best one.
                # Initial strings take the form:
                #    2:16-cr-01152-JZB USA v. Abuarar (closed 01/26/2017)
                # Attempt to pull out just the case name.
                strs = [x.split(' ', 1)[1].split('(closed', 1)[0] for x in
                        self.xml_tree.xpath('//case/@title')]
                case_index = get_closest_match_index(case_name, strs)
                if case_index is None:
                    logger.warn("Got %s candidates, but unable to find good "
                                "match to '%s'" % (case_count, case_name))
                    return None
            else:
                raise Exception("Multiple results returned but no way to "
                                "choose the right match. Try the case_name "
                                "parameter?")

        return {
            u'docket_number': force_unicode(
                self.xml_tree.xpath('//case/@number')[case_index]
            ),
            u'pacer_case_id': force_unicode(
                self.xml_tree.xpath('//case/@id')[case_index]
            ),
            # This could be further post processed to pull out the date closed
            # and a cleaner title.
            u'title': force_unicode(
                self.xml_tree.xpath('//case/@title')[case_index]
            ),
        }
