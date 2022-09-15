import re
from typing import Optional

from ..lib.log_tools import make_default_logger
from ..lib.string_utils import clean_string
from .reports import BaseReport
from .utils import make_docs1_url

logger = make_default_logger()


class DownloadConfirmationPage(BaseReport):
    """An object for querying and parsing appellate PACER documents confirmation
    download page.
    """

    def __init__(self, court_id, pacer_session=None):
        super().__init__(court_id, pacer_session)

    def query(self, pacer_doc_id):
        """Query the "confirmation download page" endpoint and set the results
        to self.response.

        :param pacer_doc_id: The internal PACER document ID for the item.
        :return: a request response object
        """

        assert (
            self.session is not None
        ), "session attribute of DownloadConfirmationPage cannot be None."

        # Make the NDA document URL
        url = make_docs1_url(self.court_id, pacer_doc_id)

        logger.info("Querying the confirmation page endpoint at URL: %s", url)
        self.response = self.session.get(url)
        self.parse()

    @property
    def data(self):
        """Get data back from the query for the matching document entry.

        :return: If lookup fails, an empty dict. Else, a dict containing the
        following fields:
            - document_number: The document number we're working with.

        See the JSON objects in the tests for more examples.
        """
        if self.is_valid is False:
            return {}

        result = {
            "document_number": self._get_document_number(),
        }
        if result["document_number"] is None:
            # Abort. If we cannot get a document number return a empy dict.
            return {}

        return result

    def _get_document_number(self) -> Optional[str]:
        """Get the document number for an item.

        :return: The PACER document number if available, otherwise None.
        """

        path = '//strong[contains(., "Document: PDF Document")]'
        try:
            document_and_case_number = self.tree.xpath(f"{path}")[
                0
            ].text_content()
        except IndexError:
            return None

        regex = r", Document:([^\)]*)"
        document_number = re.findall(regex, document_and_case_number)
        if document_number:
            return clean_string(document_number[0])
        else:
            return None
