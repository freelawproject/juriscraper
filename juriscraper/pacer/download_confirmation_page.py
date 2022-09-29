import re
from typing import Optional

from ..lib.log_tools import make_default_logger
from ..lib.string_utils import clean_string, convert_date_string, force_unicode
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
        url = make_docs1_url(self.court_id, pacer_doc_id, True)

        logger.info("Querying the confirmation page endpoint at URL: %s", url)
        self.response = self.session.get(url)
        self.parse()

    @property
    def data(self):
        """Get data back from the query for the matching document entry.

        :return: If lookup fails, an empty dict. Else, a dict containing the
        following fields:
            - document_number: The document number we're working with
            - docket_number: The docket case number we're working with
            - cost: The document cost we're working with
            - billable_pages: The document billable pages we're working with
            - document_description: The document description we're working with
            - transaction_date: The document transaction date we're working with

        See the JSON objects in the tests for more examples.
        """
        if self.is_valid is False:
            return {}

        document_number = self._get_document_number()
        if document_number is None:
            # Abort. If we cannot get a document number return a empy dict.
            # It's not a valid confirmation page.
            return {}

        return {
            "document_number": document_number,
            "docket_number": self._get_docket_number(),
            "cost": self._get_document_cost(),
            "billable_pages": self._get_billable_pages(),
            "document_description": self._get_document_description(),
            "transaction_date": self._get_transaction_date(),
        }

    def _get_document_number(self) -> Optional[str]:
        """Get the document number for an item.

        :return: The PACER document number if available, otherwise None.
        """

        try:
            document_and_case_number = self.tree.xpath(
                '//strong[contains(., "Document: PDF Document")]'
            )[0].text_content()
        except IndexError:
            return None

        regex = r", Document:([^\)]*)"
        document_number = re.findall(regex, document_and_case_number)
        if document_number:
            return clean_string(document_number[0])
        return None

    def _get_document_cost(self) -> Optional[str]:
        """Get the document cost for an item.

        :return: The PACER document cost if available, otherwise None.
        """
        try:
            cost_str = self.tree.re_xpath(
                '//*[re:match(text(), "Cost:")]/'
                "/ancestor::th[1]/following-sibling::td[1]/font[1]"
            )[0].text_content()
        except IndexError:
            return None

        if cost_str:
            return cost_str
        return None

    def _get_docket_number(self) -> Optional[str]:
        """Get the docket number for an item.

        :return: The PACER docket number if available, otherwise None.
        """

        try:
            document_and_case_number = self.tree.xpath(
                '//strong[contains(., "Document: PDF Document")]'
            )[0].text_content()
        except IndexError:
            return None

        regex = r"Case:([^\,]*)"
        docket_number = re.findall(regex, document_and_case_number)
        if docket_number:
            return clean_string(docket_number[0])
        return None

    def _get_billable_pages(self) -> Optional[str]:
        """Get the document billable pages.

        :return: The document billable pages if available, otherwise None.
        """
        try:
            billable_pages_str = self.tree.re_xpath(
                '//*[re:match(text(), "Billable Pages:")]/'
                "/ancestor::th[1]/following-sibling::td[1]/font[1]"
            )[0].text_content()
        except IndexError:
            return None

        if billable_pages_str:
            return billable_pages_str
        return None

    def _get_document_description(self) -> Optional[str]:
        """Get the document description for an item.

        :return: The PACER document description if available, otherwise None.
        """
        try:
            document_description_str = self.tree.re_xpath(
                '//*[re:match(text(), "Description:")]/'
                "/ancestor::th[1]/following-sibling::td[1]/font[1]"
            )[0].text_content()
        except IndexError:
            return None

        if document_description_str:
            return document_description_str
        return None

    def _get_transaction_date(self) -> Optional[str]:
        """Get the PACER transaction date.

        :return: The PACER transaction date if available, otherwise None.
        """

        try:
            transaction_date_str = self.tree.re_xpath(
                '//*[re:match(text(), "Transaction Receipt")]/'
                "/ancestor::tr[1]/following-sibling::tr[3]"
            )[0].text_content()
        except IndexError:
            return None

        if "-" in transaction_date_str:
            # Some courts include additional data besides the date time:
            # 5th Circuit - Appellate - 08/30/2022 13:48:21
            # 2th Circuit - 08/30/2022 13:48:21
            # datetime it's always at the end.
            transaction_date_str = transaction_date_str.split("-")[-1]

        transaction_date_str = force_unicode(transaction_date_str)
        transaction_date_str = convert_date_string(
            transaction_date_str, datetime=True
        )

        if transaction_date_str:
            return transaction_date_str
        return None
