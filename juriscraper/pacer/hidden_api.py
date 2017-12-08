from lxml import etree

from .reports import BaseReport
from .utils import get_pacer_doc_id_from_doc1_url
from ..lib.diff_tools import get_closest_match_index
from ..lib.exceptions import ParsingException
from ..lib.log_tools import make_default_logger
from ..lib.string_utils import force_unicode

logger = make_default_logger()


class PossibleCaseNumberApi(BaseReport):
    """Tools for gathering data from the "Possible case numbers" hidden API.

    This API takes a docket number and a court as input, and returns an XML
    object with the pacer_case_id, title, normalized docket number, and a few
    other things.

    This API is normally used via AJAX in the front end of PACER when you put a
    docket number into the docket report search box.
    """
    PATH = 'cgi-bin/possible_case_numbers.pl'

    def query(self, docket_number):
        """Query the "possible case numbers" endpoint and return the results.

        :param docket_number: A string representing a docket number
        :return: a request response object
        """
        assert self.session is not None, \
            "session attribute of PossibleCaseNUmberApi cannot be None."
        url = "%s?%s" % (self.url, docket_number)
        logger.info(u'Querying the possible case number endpoint at URL: %s' %
                    url)
        self.response = self.session.get(url)
        self.parse()

    def _parse_text(self, text):
        """Parse the text of the response object and put it in self.tree.

        Use an XML parser instead of the normal HTML one.
        """
        self.tree = etree.fromstring(text)

    def data(self, case_name=None):
        """Get data back from this query for the matching case.

        :param case_name: This endpoint can return multiple cases for a given
        query. If a case name is provided, and more than one case is returned,
        we will try to identify the most similar case.
        """
        case_count = self.tree.xpath('count(//case)')
        if case_count == 0:
            try:
                msg = self.tree.xpath('//message/@text')[0]
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
                        self.tree.xpath('//case/@title')]
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
                self.tree.xpath('//case/@number')[case_index]
            ),
            u'pacer_case_id': force_unicode(
                self.tree.xpath('//case/@id')[case_index]
            ),
            # This could be further post processed to pull out the date closed
            # and a cleaner title.
            u'title': force_unicode(
                self.tree.xpath('//case/@title')[case_index]
            ),
        }


class ShowCaseDocApi(BaseReport):
    """Lookup a pacer_doc_id using the pacer_case_id and document_number

    There is a URL that's available at:

        https://ecf.nyed.uscourts.gov/cgi-bin/show_case_doc?90,406590,,

    That takes a document number and case number, and performs a redirect to a
    doc1 URL. Thus, using this API you can get the pacer_doc_id value for an
    item using only the document_number, pacer_case_id, and (optionally) the
    attachment_number.
    """
    PATH = 'cgi-bin/show_case_doc'

    def __init__(self, court_id, pacer_session=None):
        assert not court_id.endswith('b'), \
            "This API is not available at bankruptcy courts."
        super(ShowCaseDocApi, self).__init__(court_id, pacer_session)

    def query(self, pacer_case_id, document_number, attachment_number=''):
        """Query the show_case_doc endpoint and return the normalized doc1
        number.

        :param pacer_case_id: The internal PACER case ID for the case.
        :param document_number: The document number on the docket for the item.
        :param attachment_number: The attachment number of the item on the
        attachment page.
        """
        assert self.session is not None, \
            "session attribute of ShowCaseDocApi cannot be None."
        url = ('{url}?'
               '{document_number},'
               '{pacer_case_id},'
               '{attachment_number},,'.format(
                    url=self.url,
                    document_number=document_number,
                    pacer_case_id=pacer_case_id,
                    attachment_number=attachment_number,
               ))
        logger.info(u'Querying the show_doc_url endpoint with URL: %s' % url)
        # Only do a head request, else we get text content we don't need.
        self.response = self.session.head(url, allow_redirects=True)
        self.parse()

    def _parse_text(self, text):
        """Just a stub. No parsing needed here."""
        pass

    @property
    def data(self):
        """Get the URL out of the response object."""
        url = self.response.url
        if 'doc1' in url:
            return get_pacer_doc_id_from_doc1_url(url)
        else:
            raise ParsingException("Unable to get doc1-style URL. Instead got %s" % url)
