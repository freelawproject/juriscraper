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

    PATH = "cgi-bin/possible_case_numbers.pl"

    def query(self, docket_number):
        """Query the "possible case numbers" endpoint and return the results.

        :param docket_number: A string representing a docket number
        :return: a request response object
        """
        assert (
            self.session is not None
        ), "session attribute of PossibleCaseNUmberApi cannot be None."
        url = "%s?%s" % (self.url, docket_number.lower())
        logger.info(
            u"Querying the possible case number endpoint at URL: %s" % url
        )
        self.response = self.session.get(url)
        self.parse()

    def _parse_text(self, text):
        """Parse the text of the response object and put it in self.tree.

        Use an XML parser instead of the normal HTML one.
        """
        self.tree = etree.fromstring(text)

    def data(
        self, case_name=None, office_number=None, docket_number_letters=None
    ):
        """Get data back from this query for the matching case.

        :param case_name: This endpoint can return multiple cases for a given
        query. If a case name is provided, and more than one case is returned,
        we will try to identify the most similar case.
        :param office_number: The office number where the item was litigated.
        Usually, this will show up as part of the extended docket number, before
        the colon. For example, in this instance the office number is 2:
        2:16-cr-01152-JZB. Sometimes we know the office number, for example, if
        we're using the IDB. Note that office "numbers" can sometimes be
        a letter. The numbering appears to be 1-9, then A-Z.
        :param docket_number_letters: Sometimes you'll know the letters that
        should be in the returned docket number. For example, they might be 'cr'
        or 'cv'. If you do, you can add this parameter to help filter the
        possible results based on the docket numbers returned.
        For example, if you set this to "cv", and you get back two results:
          2:16-cr-01152-JZB
          2:16-cv-01152-JZB
        You'll know that it's the second result because cv means civil. Again
        this is something you might know if you're using the IDB. These are
        some known values:
         - cv - Civil
         - cr - Criminal
         - ap - Appellate (bankruptcy?)
         - mdl - Multi-district litigation
         - bk - Bankruptcy
        There are others too, feel free to add them if you know them.
        """
        case_count = self.tree.xpath("count(//case)")
        nodes = self.tree.xpath("//case")
        if case_count == 0:
            try:
                msg = self.tree.xpath("//message/@text")[0]
            except IndexError:
                pass
            else:
                if "Cannot find case" in msg or "Case Under Seal" in msg:
                    logger.info("Cannot find case.")
                    return None
            raise ParsingException(
                "Unknown XML content in " "PossibleCaseNumberApi result."
            )
        elif case_count == 1:
            # Only one node, all set to go.
            pass
        elif case_count > 1:
            # Filter by things we know
            if office_number is not None:
                # Remove items by docket number, if they lead with something
                # other than the correct office number.
                def correct_office_number(node):
                    try:
                        number = node.xpath("./@number")[0].split(":")[0]
                    except IndexError:
                        # Don't filter...something went wrong.
                        return True
                    return number == office_number

                nodes = list(filter(correct_office_number, nodes))

            if len(nodes) > 1 and docket_number_letters is not None:
                # Remove items by docket number, if they have cv or cr.
                f = (
                    lambda node: docket_number_letters
                    in node.xpath("./@number")[0]
                )
                nodes = list(filter(f, nodes))

            if len(nodes) > 1:
                # If we only have sequential defendant attributes, pick the
                # lowest one. The lowest one tends to be the main case, and the
                # others are additional dockets for specific defendants.
                try:
                    attribute = "@defendant"
                    ids = sorted(
                        [int(x.xpath("./%s" % attribute)[0]) for x in nodes]
                    )
                except IndexError:
                    # No defendant attribute one of the nodes. Try by
                    # pacer_case_id instead. We used to do this by default,
                    # instead of defendant number, but it is not always
                    # sequential.
                    attribute = "@id"
                    ids = sorted(
                        [int(x.xpath("./%s" % attribute)[0]) for x in nodes]
                    )

                missing_ids = set(range(ids[0], ids[-1] + 1)).difference(ids)
                if len(missing_ids) > 0:
                    # The IDs are not sequential. Can't use this technique.
                    pass
                else:
                    nodes = self.tree.xpath(
                        "//case[%s=%s]" % (attribute, ids[0])
                    )

            if len(nodes) > 1 and case_name is not None:
                # Disambiguate the possible case nodes to find the best one.
                # Initial strings take the form:
                #    2:16-cr-01152-JZB USA v. Abuarar (closed 01/26/2017)
                # Attempt to pull out just the case name.
                title_attrs = [node.xpath("./@title")[0] for node in nodes]
                strs = [
                    title.split(" ", 1)[1].split("(closed", 1)[0]
                    for title in title_attrs
                ]
                case_index = get_closest_match_index(case_name, strs)
                if case_index is None:
                    logger.warn(
                        "Got %s candidates, but unable to find good "
                        "match to '%s'" % (len(nodes), case_name)
                    )
                else:
                    nodes = [nodes[case_index]]

            if len(nodes) > 1:
                raise ParsingException(
                    "Multiple results returned but no way to choose the right "
                    "match. Try the case_name, office_number, or "
                    "docket_number_letters parameters?"
                )

        if nodes:
            node = nodes[0]
            return {
                u"docket_number": force_unicode(node.xpath("./@number")[0]),
                u"pacer_case_id": force_unicode(node.xpath("./@id")[0]),
                # This could be further post processed to pull out the date closed
                # and a cleaner title.
                u"title": force_unicode(node.xpath("./@title")[0]),
            }
        else:
            raise ParsingException("Unable to identify case.")


class ShowCaseDocApi(BaseReport):
    """Lookup a pacer_doc_id using the pacer_case_id and document_number

    There is a URL that's available at:

        https://ecf.nyed.uscourts.gov/cgi-bin/show_case_doc?90,406590,,

    That takes a document number and case number, and performs a redirect to a
    doc1 URL. Thus, using this API you can get the pacer_doc_id value for an
    item using only the document_number, pacer_case_id, and (optionally) the
    attachment_number.
    """

    PATH = "cgi-bin/show_case_doc"

    def __init__(self, court_id, pacer_session=None):
        assert not court_id.endswith(
            "b"
        ), "This API is not available at bankruptcy courts."
        super(ShowCaseDocApi, self).__init__(court_id, pacer_session)

    def query(self, pacer_case_id, document_number, attachment_number=""):
        """Query the show_case_doc endpoint and return the normalized doc1
        number.

        :param pacer_case_id: The internal PACER case ID for the case.
        :param document_number: The document number on the docket for the item.
        :param attachment_number: The attachment number of the item on the
        attachment page.
        """
        assert (
            self.session is not None
        ), "session attribute of ShowCaseDocApi cannot be None."
        url = (
            "{url}?"
            "{document_number},"
            "{pacer_case_id},"
            "{attachment_number},,".format(
                url=self.url,
                document_number=document_number,
                pacer_case_id=pacer_case_id,
                attachment_number=attachment_number,
            )
        )
        logger.info(u"Querying the show_doc_url endpoint with URL: %s" % url)
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
        if "doc1" in url:
            return get_pacer_doc_id_from_doc1_url(url)
        else:
            raise ParsingException(
                "Unable to get doc1-style URL. Instead got %s" % url
            )
