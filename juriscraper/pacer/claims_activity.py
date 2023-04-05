import re
from datetime import date
from typing import Dict, List, Union

from lxml.html import HtmlElement

from juriscraper.pacer.reports import BaseReport

from ..lib.log_tools import make_default_logger
from ..lib.string_utils import convert_date_string, force_unicode, harmonize
from ..lib.utils import clean_court_object
from .docket_report import BaseDocketReport
from .utils import get_pacer_case_id_from_doc1_url

logger = make_default_logger()


class ClaimsActivity(BaseDocketReport, BaseReport):
    """Query and parse the claims activity."""

    PATH = "cgi-bin/ClaimsActRpt.pl"
    CACHE_ATTRS = ["claims", "metadata"]
    ERROR_STRINGS = BaseReport.ERROR_STRINGS + [
        "No claims entries found",
        "Security violation: You do not have access rights to this program",
    ]

    def __init__(self, court_id, pacer_session=None):
        BaseDocketReport.__init__(self, court_id)
        BaseReport.__init__(self, court_id, pacer_session)

        self._clear_caches()
        self._metadata = None
        self._claims = None
        assert court_id.endswith(
            "b"
        ), "Unable to create object. Must use bankruptcy court abbreviation."

    @property
    def data(self):
        """Get all the data back from this endpoint."""
        if self.is_valid is False:
            return {}

        data = self.metadata.copy()
        return data

    @property
    def metadata(self):
        """
        Each claim table looks like this:

        --------------------+------------+---------------------
        Case and claim data | Claim data |  Case and claim data
        -------------------------------------------------------
        Claim data
        -------------------------------------------------------
        Claim data (no always present)
        -------------------------------------------------------

        So first we parse each colum of the first row, then second and third
        row, finding the fields for the case and the claim.
        """

        if self.is_valid is False:
            return {}

        if self._metadata is not None:
            return self._metadata

        data = []

        field_mappings_case = {
            "title": "case_name",
            "case": "docket_number",
            "office": "office",
            "chapter": "chapter",
            "judge": "assigned_to_str",
            "trustee": "trustee_str",
            "last_date_to_file_claims": "last_date_to_file_claims",
            "last_date_to_file_govt": "last_date_to_file_govt",
        }
        field_mappings_claim = {
            "amends_no": "amends_no",
            "amount_claimed": "amount_claimed",
            "amount_allowed": "amount_allowed",
            "secured_claimed": "secured_claimed",
            "priority_claimed": "priority_claimed",
            "creditor_name_address": "creditor_name_address",
            "description": "description",
            "creditor_id": "creditor_id",
            "filed": "date_filed",
            "entered": "date_entered",
            "entered_by": "entered_by",
            "filed_by": "filed_by",
            "status": "status",
            "remarks": "remarks",
        }

        claim_tables = self.tree.xpath('//table[@class="complexReport"]')
        for claim_table in claim_tables:
            meta_data = {
                "court_id": self.court_id,
            }
            claim = {}

            label_nodes = claim_table.xpath("(.//tr)[1]/td[1]/text()")
            # Parse case and claim data from row 1 column 1.
            for label_node in label_nodes:
                meta_data.update(
                    self._get_label_value_pair_from_string(
                        label_node, field_mappings_case
                    )
                )
                claim.update(
                    self._get_label_value_pair_from_string(
                        label_node, field_mappings_claim
                    )
                )

            self._parse_case_name_and_docket_number(meta_data, claim_table)

            claim_anchor_nodes = claim_table.xpath("(.//tr)[1]/td[1]/b/a")
            claim.update(self._get_claim_data_from_anchors(claim_anchor_nodes))

            # Parse claim data from row 1 column 2.
            label_nodes = claim_table.xpath("(.//tr)[1]/td[2]/text()")
            for label_node in label_nodes:
                claim.update(
                    self._get_label_value_pair_from_string(
                        label_node, field_mappings_claim
                    )
                )

            # Parse case and claim data from row 1 column 3.
            label_nodes = claim_table.xpath("(.//tr)[1]/td[3]/text()")
            for label_node in label_nodes:
                meta_data.update(
                    self._get_label_value_pair_from_string(
                        label_node, field_mappings_case
                    )
                )
                claim.update(
                    self._get_label_value_pair_from_string(
                        label_node, field_mappings_claim
                    )
                )

            # Parse claim data from row 2.
            label_nodes = claim_table.xpath("(.//tr)[2]/td[1]/text()")
            for label_node in label_nodes:
                claim.update(
                    self._get_label_value_pair_from_string(
                        label_node, field_mappings_claim
                    )
                )

            # Parse claim data from row 3.
            label_nodes = claim_table.xpath("(.//tr)[3]/td[1]/text()")
            for label_node in label_nodes:
                claim.update(
                    self._get_label_value_pair_from_string(
                        label_node, field_mappings_claim
                    )
                )

            meta_data["claim"] = claim
            data.append(meta_data)

            # Fill non present values in the report in order to standarize
            # fields in the report.
            self._fill_non_present_values_as_empty(
                field_mappings_case, meta_data
            )
            self._fill_non_present_values_as_empty(
                field_mappings_claim, meta_data["claim"]
            )

        data = clean_court_object(data)
        self._metadata = data
        return data

    def _fill_non_present_values_as_empty(
        self,
        field_mappings: Dict[str, str],
        meta_data: Dict[str, Union[str, date, None, List[Dict[str, str]]]],
    ) -> None:
        """Fill claim missing values in meta_data with empty values if they are
        not present.

        :param field_mappings: A dictionary of mappings field names.
        :param meta_data: A dictionary containing the metadata for the claim.
        :return: None, meta_data is modified in place.
        """

        for key, value in field_mappings.items():
            if value not in meta_data:
                if value.startswith("date_") or value.startswith("last_date_"):
                    meta_data[value] = None
                else:
                    meta_data[value] = ""

    def _parse_case_name_and_docket_number(
        self,
        meta_data: Dict[str, Union[str, date, None, List[Dict[str, str]]]],
        claim_table: HtmlElement,
    ) -> None:
        """Parses the case name and docket number from the provided meta_data
        dictionary and claim_table HTML element.

        :param meta_data: A dictionary containing the case metadata.
        :param claim_table: The lxml.HtmlElement claim_table
        :return: None, the meta_data dict is updated in place.
        """
        meta_data["case_name"] = harmonize(meta_data["case_name"])

        docket_number = meta_data.get("docket_number")
        if docket_number:
            meta_data["docket_number"] = self._clean_docket_number(
                docket_number
            )
        else:
            docket_number = claim_table.xpath("(.//tr)[1]/td[1]/a//text()")[0]
            meta_data["docket_number"] = self._clean_docket_number(
                docket_number
            )

    def _clean_docket_number(self, docket_number: str) -> str:
        """Strip the judge initials off docket numbers, and do any other
        similar cleanup.

        :param: docket_number: A string docket number to clean.
        :return: The docket_number cleaned.
        """

        # Uses both b/c sometimes the bankr. cases have a dist-style docket
        # number.
        regexes = [
            self.docket_number_dist_regex,
            self.docket_number_bankr_regex,
        ]
        for regex in regexes:
            match = regex.search(docket_number)
            if match:
                return match.group(1)

        return docket_number

    def _get_claim_data_from_anchors(
        self, anchor_nodes: List[HtmlElement]
    ) -> Dict[str, Union[str, List[Dict[str, str]]]]:
        """Retrieves claim data from a list of HTML anchor elements.

        :param anchor_nodes: A list of HTML anchor elements that contain
        information about the claim.

        :return: A dict with the claim data and claim attachments.
        """

        claim = {}
        attachments = []
        for i, anchor in enumerate(anchor_nodes):
            document_url = (
                anchor.xpath("./@href")[0] if anchor is not None else None
            )
            if i == 0:
                claim["pacer_case_id"] = get_pacer_case_id_from_doc1_url(
                    document_url
                )
                claim["claim_id"] = self.get_pacer_claim_id_from_claim_url(
                    document_url
                )
                claim["claim_number"] = self.get_claim_number_from_claim_url(
                    document_url
                )
            else:
                claim_att = {}
                claim_att["pacer_case_id"] = get_pacer_case_id_from_doc1_url(
                    document_url
                )
                claim_att["claim_id"] = self.get_pacer_claim_id_from_claim_url(
                    document_url
                )
                claim_att[
                    "claim_number"
                ] = self.get_claim_number_from_claim_url(document_url)
                claim_att["short_description"] = anchor.text_content()
                claim_att[
                    "claim_doc_seq"
                ] = self.get_claim_doc_seq_from_claim_url(document_url)

                attachments.append(claim_att)

        claim["attachments"] = attachments
        return claim

    @staticmethod
    def get_pacer_claim_id_from_claim_url(url: str) -> Union[str, None]:
        """Extract the caseid from the doc1 URL."""
        match = re.search(r"claim_id=(\d+)", url)
        if match:
            return match.group(1)
        else:
            return None

    @staticmethod
    def get_claim_number_from_claim_url(url: str) -> Union[str, None]:
        """Extract the caseid from the doc1 URL."""
        match = re.search(r"claim_num=(\d+-\d+)", url)
        if match:
            return match.group(1)
        else:
            return None

    @staticmethod
    def get_claim_doc_seq_from_claim_url(url: str) -> Union[str, None]:
        """Extract the caseid from the doc1 URL."""
        match = re.search(r"claim_doc_seq=(\d+)", url)
        if match:
            return match.group(1)
        else:
            return None

    @staticmethod
    def _get_label_value_pair_from_string(
        string: str, field_mappings: Dict[str, str]
    ) -> Dict[str, Union[str, date, None]]:
        """Get the field name and value from a string.

        e.g: Case: 3:23-bk-10722
        :param string: The string where to extract the label and value.
        :param field_mappings: A dict mapping PACER labels to Juriscraper ones.
        :return a dict with a k-v mapping between a label and its value.
        """

        splited_string = string.split(":", 1)

        if len(splited_string) <= 1:
            return {}

        label = splited_string[0]
        value = splited_string[1]

        label = (
            label.strip()
            .lower()
            .replace(" ", "_")
            .replace("/", "_")
            .replace("\xa0", "_")  # Non-breaking space
            .replace("(", "")
            .replace(")", "")
            .rstrip(":")
        )
        label = field_mappings.get(label, None)

        if not label:
            return {}

        value = value.strip()
        value = value.lstrip(":").strip()
        if label.startswith("date_") or label.startswith("last_date_"):
            if value:
                data = {label: convert_date_string(value)}
            else:
                data = {label: None}
        else:
            data = {label: force_unicode(value)}
        return data

    def query(
        self,
        pacer_case_id: str,
        docket_number: str,
        creditor_name: str,
        date_start: date = None,
        date_end: date = None,
    ):
        """Query the claims activity and return the results.

        :param pacer_case_id: The internal PACER ID for the case.
        :param docket_number: A docket number to look up. Something like
        2:17-bk-39239.
        :param creditor_name: The creditor name to look up.
        :param date_start: The earliest claim entry you wish to have. Default
        is 1960-01-01 (before anything was put in PACER)
        :param date_end: The latest claim entry you with to have. Default is
        tomorrow.

        :return: request response object
        """
        assert (
            self.session is not None
        ), "session attribute of ClaimsActivity cannot be None."

        params = {
            "all_case_ids": pacer_case_id,
            # Whether to filter by filed date or entered date. Parser only
            # currently supports filed date.
            "sort1": "case number",
            "sort2": "claim number",
            # This field seems to be required while 'all_case_ids' is not.
            "case_num": docket_number,
            "creditor": creditor_name,
        }
        if date_start:
            params["entered_from"] = date_start.strftime("%m/%d/%Y")
        else:
            # Set the default
            params["entered_from"] = "1/1/1960"
        if date_end:
            params["entered_to"] = date_end.strftime("%m/%d/%Y")

        logger.info(
            "Querying claims activy for case ID '%s' in court '%s' "
            "with params %s",
            pacer_case_id,
            self.court_id,
            params,
        )

        if self.court_id == "insb":
            # The POST param wildcard 1-L_1_0-1 doesn't work for insb.
            # It throws a 500 error. 1-L_945_0-1 doesn't work either.
            # The only approach that seems to work is using one of the params
            # generated in cgi-bin/ClaimsActRpt.pl
            # Unfortunately this might stop working since it seems to expire
            # or might be linked to the PACER session.
            post_param = "124892645626785-L_945_0-1"
        else:
            post_param = "1-L_1_0-1"

        self.response = self.session.post(
            f"{self.url}?{post_param}", data=params
        )
        self.parse()
