from typing import TYPE_CHECKING

from lxml import etree
from pydantic import ConfigDict, TypeAdapter, with_config
from typing_extensions import TypedDict, override

from juriscraper.lib.diff_tools import get_closest_match_index
from juriscraper.lib.exceptions import ParsingException
from juriscraper.lib.log_tools import make_default_logger

from .reports import BaseReport
from .utils import get_pacer_doc_id_from_doc1_url

logger = make_default_logger()

if TYPE_CHECKING:
    from .http import PacerSession


class PossibleCaseNumberApi(BaseReport):
    """Tools for gathering data from the "Possible case numbers" hidden API.

    This API takes a docket number and a court as input, and returns an XML
    object with the pacer_case_id, title, normalized docket number, and a few
    other things.

    This API is normally used via AJAX in the front end of PACER when you put a
    docket number into the docket report search box.
    """

    PATH = "cgi-bin/possible_case_numbers.pl"

    async def query(self, docket_number: str) -> None:
        """Query the "possible case numbers" endpoint and return the results.

        :param docket_number: A string representing a docket number
        :return: a request response object
        """
        if self.session is None:
            raise ValueError(
                "session attribute of PossibleCaseNUmberApi cannot be None."
            )
        url = f"{self.url}?{docket_number.lower()}"
        logger.info(
            f"Querying the possible case number endpoint at URL: {url}"
        )
        self.response = await self.session.get(url)
        self.parse()

    @override
    def _parse_text(self, text: str) -> None:
        """Parse the text of the response object and put it in self.tree.

        Use an XML parser instead of the normal HTML one.
        """
        self.tree = None
        self.tree = etree.fromstring(text)

    def data(
        self,
        case_name: str | None = None,
        office_number: str | None = None,
        docket_number_letters: str | None = None,
    ) -> dict[str, str] | None:
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
        if self.tree is None:
            raise ValueError("Parse a response before selecting a case.")
        nodes: list[etree._Element] = self.tree.xpath("//case")
        case_count = len(nodes)
        if case_count == 0:
            try:
                messages: list[str] = self.tree.xpath("//message/@text")
                msg = messages[0]
            except IndexError:
                pass
            else:
                if "Cannot find case" in msg or "Case Under Seal" in msg:
                    logger.info("Cannot find case.")
                    return None
            raise ParsingException(
                "Unknown XML content in PossibleCaseNumberApi result."
            )
        elif case_count == 1:
            # Only one node, all set to go.
            pass
        elif case_count > 1:
            # Filter by things we know
            if office_number is not None:
                # Remove items by docket number, if they lead with something
                # other than the correct office number.
                def correct_office_number(node: etree._Element) -> bool:
                    number = node.get("number")
                    if number is None:
                        # Don't filter...something went wrong.
                        return True
                    return number.split(":")[0] == office_number

                nodes = list(filter(correct_office_number, nodes))

            if len(nodes) > 1 and docket_number_letters is not None:
                # Remove items by docket number, if they have cv or cr.
                filtered_nodes = []
                for node in nodes:
                    number = node.get("number")
                    if number is None:
                        raise ParsingException(
                            "Case result is missing its 'number' attribute."
                        )
                    if docket_number_letters in number:
                        filtered_nodes.append(node)
                nodes = filtered_nodes

            if len(nodes) > 1:
                # If we only have sequential defendant attributes, pick the
                # lowest one. The lowest one tends to be the main case, and the
                # others are additional dockets for specific defendants.
                attribute = "defendant"
                if any(node.get(attribute) is None for node in nodes):
                    # No defendant attribute one of the nodes. Try by
                    # pacer_case_id instead. We used to do this by default,
                    # instead of defendant number, but it is not always
                    # sequential.
                    attribute = "id"
                ids = []
                for node in nodes:
                    value = node.get(attribute)
                    if value is None:
                        raise ParsingException(
                            f"Case result is missing its {attribute!r} attribute."
                        )
                    ids.append(int(value))
                ids.sort()

                missing_ids = set(range(ids[0], ids[-1] + 1)).difference(ids)
                if len(missing_ids) > 0:
                    # The IDs are not sequential. Can't use this technique.
                    pass
                else:
                    nodes = self.tree.xpath(f"//case[@{attribute}={ids[0]}]")

            if len(nodes) > 1 and case_name is not None:
                # Disambiguate the possible case nodes to find the best one.
                # Initial strings take the form:
                #    2:16-cr-01152-JZB USA v. Abuarar (closed 01/26/2017)
                # Attempt to pull out just the case name.
                title_attrs = []
                for node in nodes:
                    title = node.get("title")
                    if title is None:
                        raise ParsingException(
                            "Case result is missing its 'title' attribute."
                        )
                    title_attrs.append(title)
                strs = [
                    title.split(" ", 1)[1].split("(closed", 1)[0]
                    for title in title_attrs
                ]
                case_index = get_closest_match_index(case_name, strs)
                if case_index is None:
                    logger.warning(
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

        if bool(nodes):
            node = nodes[0]
            for attribute in ("number", "id", "title"):
                if node.get(attribute) is None:
                    raise ParsingException(
                        f"Case result is missing its {attribute!r} attribute."
                    )
            return {
                "docket_number": node.attrib["number"],
                "pacer_case_id": node.attrib["id"],
                # This could be further post processed to pull out the date closed
                # and a cleaner title.
                "title": node.attrib["title"],
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

    def __init__(
        self, court_id: str, pacer_session: "PacerSession | None" = None
    ) -> None:
        if court_id.endswith("b"):
            raise ValueError("This API is not available at bankruptcy courts.")
        super().__init__(court_id, pacer_session)

    async def query(
        self,
        pacer_case_id: str | int,
        document_number: str | int,
        attachment_number: str | int = "",
    ) -> None:
        """Query the show_case_doc endpoint and return the normalized doc1
        number.

        :param pacer_case_id: The internal PACER case ID for the case.
        :param document_number: The document number on the docket for the item.
        :param attachment_number: The attachment number of the item on the
        attachment page.
        """
        if self.session is None:
            raise ValueError(
                "session attribute of ShowCaseDocApi cannot be None."
            )
        url = (
            f"{self.url}?"
            f"{document_number},"
            f"{pacer_case_id},"
            f"{attachment_number},,"
        )
        logger.info(f"Querying the show_doc_url endpoint with URL: {url}")
        # we use get request because nysd court disabled all head requests
        # and bans by IP in case head request is made
        self.response = await self.session.get(url, follow_redirects=True)
        self.parse()

    @override
    def _parse_text(self, text: str) -> None:
        """Just a stub. No parsing needed here."""
        pass

    @property
    def data(self) -> str:
        """Get the URL out of the response object."""
        if self.response is None:
            raise ValueError(
                "A response is required to retrieve a document URL."
            )
        url = str(self.response.url)
        if "doc1" in url:
            return get_pacer_doc_id_from_doc1_url(url)
        else:
            raise ParsingException(
                f"Unable to get doc1-style URL. Instead got {url}"
            )


@with_config(ConfigDict(extra="allow"))
class AcmsCaseSearchResult(TypedDict, total=False):
    pcx_caseid: str | None


class AcmsCaseSearch(BaseReport):
    """
    Looks up an ACMS case by its docket number using the CaseSearch API.
    """

    async def query(self, docket_number: str) -> None:
        if self.session is None:
            raise ValueError(
                "session attribute of AcmsCaseSearch cannot be None."
            )
        url = f"https://{self.court_id}-showdocservices.azurewebsites.us/api/CaseSearch/{docket_number}"
        logger.info(f"Querying the CaseSearch endpoint with URL: {url}")
        self.response = await self.session.get(
            url, params={"exactMatch": True}
        )
        self.parse()

    @override
    def _parse_text(self, text: str) -> None:
        """Just a stub. No parsing needed here."""
        pass

    @property
    def data(self) -> AcmsCaseSearchResult:
        """
        Retrieves the parsed case data from the API response.

        The returned dictionary contains the following keys:
            - '@odata.etag'
            - 'pcx_caseid'
            - 'pcx_casenumber'
            - 'pcx_name'
            - 'pcx_istestcase'

        :return: A dictionary containing the case data, or an empty dictionary
                 if no data is found, the response is malformed, or an error
                 occurred.
        """
        if self.response is None:
            raise ValueError("A response is required to retrieve case data.")
        case_data: object = self.response.json()
        if not bool(case_data):
            return {}
        return TypeAdapter(list[AcmsCaseSearchResult]).validate_python(
            case_data, strict=True
        )[0]
