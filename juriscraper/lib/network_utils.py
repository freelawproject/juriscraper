import random
import ssl
import time
from datetime import datetime
from typing import Any

from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util import create_urllib3_context

from juriscraper.lib.log_tools import make_default_logger

logger = make_default_logger()


class SSLAdapter(HTTPAdapter):
    def __init__(
        self, ssl_version=ssl.PROTOCOL_TLSv1_2, ciphers=None, **kwargs
    ):
        self.ssl_version = ssl_version or ssl.PROTOCOL_TLS
        self.ssl_context = create_urllib3_context(
            ssl_version=self.ssl_version, ciphers=ciphers
        )
        super().__init__(**kwargs)

    def init_poolmanager(self, *args, **kwargs):
        kwargs["ssl_context"] = self.ssl_context
        return super().init_poolmanager(*args, **kwargs)


def add_delay(delay=0, deviation=0):
    """Create a semi-random delay.

    Delay is the number of seconds your program will be stopped for, and
    deviation is the number of seconds that the delay can vary.
    """
    from juriscraper.AbstractSite import logger

    duration = random.randrange(delay - deviation, delay + deviation)
    logger.info(f"Adding a delay of {duration} seconds. Please wait.")
    time.sleep(duration)


class AcmsApiClient:
    """
    Client for interacting with the court's API, responsible for making requests
    and mapping raw responses to a standardized format.
    """

    BASE_URL_TEMPLATE = (
        "https://{court_id}-showdocservices.azurewebsites.us/api/"
    )
    CASE_DETAILS_ENDPOINT = "CaseDetailsByCaseId/{case_id}"
    DOCKET_ENTRIES_ENDPOINT = "DocketEntriesByCaseId/{case_id}"
    ATTACHMENTS_ENDPOINT = "DocketEntryDocumentsByDocketId/{entry_id}"

    def __init__(self, session: Session, court_id: str):
        self.session = session
        self.court_id = court_id
        self.base_url = self.BASE_URL_TEMPLATE.format(court_id=self.court_id)

    def _map_case_details_response(
        self, raw_data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Maps the raw API response for case details to a standardized dictionary
        format.

        This method extracts and renames specific fields relevant to existing
        logic for parties and metadata. Not all fields from the raw response are
        mapped.

        :param raw_data: The raw dictionary response from the case details API.
        :return: A dictionary containing the mapped case details.
        """
        case_details = {
            "caseId": raw_data.get("pcx_caseid"),
            "caseNumber": raw_data.get("pcx_casenumber"),
            "originatingCaseNumber": raw_data.get("pcx_originatingcasenumber"),
            "caseFormType": raw_data.get("caseFormType"),
            "name": raw_data.get("pcx_name"),
            "caseOpened": raw_data.get("acms_caseopened"),
            "aNumber": raw_data.get("acms_anumber"),
            "receivedDate": raw_data.get("pcx_receiveddate"),
            "decisionDate": raw_data.get("acms_decisiondate"),
            "partyAttorneyList": raw_data.get("acms_partyattorneylist"),
            "shortCaption": raw_data.get("acms_raw_html"),
            "caseType": (
                raw_data["pcx_casetype"].get("pcx_casetypename")
                if raw_data.get("pcx_casetype")
                else None
            ),
            "caseSubType": (
                raw_data["pcx_casesubtype"].get("pcx_casesubtypename")
                if raw_data.get("pcx_casesubtype")
                else None
            ),
            "caseSubSubType": (
                raw_data["pcx_casesubsubtype"].get("pcx_casesubsubtypename")
                if raw_data.get("pcx_casesubsubtype")
                else None
            ),
            "districtCourtName": (
                raw_data["acms_DistrictCourt"].get("pcx_districtname")
                if raw_data.get("acms_DistrictCourt")
                else None
            ),
            "feeStatus": (
                raw_data["acms_feestatusid"].get("acms_feestatusname")
                if raw_data.get("acms_feestatusid")
                else None
            ),
            "byteCount": (
                int(raw_data.get("byteCount"))
                if raw_data.get("byteCount")
                else None
            ),
            "natureOfSuit": (
                raw_data["acms_NatureofSuit"].get("acms_name")
                if raw_data.get("acms_NatureofSuit")
                else None
            ),
        }

        if raw_data.get("pcx_court"):
            case_details["court"] = {
                "name": raw_data["pcx_court"].get("pcx_name"),
                "abbreviatedName": raw_data["pcx_court"].get(
                    "acms_abbreviatedname"
                ),
            }

        return case_details

    def _map_docket_entries_response(
        self, raw_data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Maps the raw API response for docket entry details to a standardized
        format.

        :param raw_data: The raw dictionary response from the docket entries API
        :return: A dictionary containing the mapped data for entries.
        """
        docket_info = {
            "isCaseSealed": raw_data.get("isCaseSealed"),
            "isUserCaseParticipant": raw_data.get("isUserCaseParticipant"),
            "byteCount": (
                int(raw_data.get("byteCount"))
                if raw_data.get("byteCount")
                else None
            ),
        }

        entries = []
        for row in raw_data.get("matchingDocketEntries", []):
            entry_data = {
                "endDate": row.get("pcx_enddate"),
                "endDateFormatted": datetime.strptime(
                    row.get("pcx_enddate"), "%Y-%m-%d"
                ).strftime("%m/%d/%Y"),
                "entryNumber": row.get("pcx_entrynumber"),
                "docketEntryText": row.get("pcx_eventdescription"),
                "docketEntryId": row.get("pcx_eventid"),
                "createdOn": row.get("createdon"),
                "documentCount": row.get("documentCount"),
                "pageCount": row.get("pageCount"),
                "fileSize": row.get("fileSize"),
                "restrictedPartyFilingDocketEntry": row.get(
                    "restrictedPartyFilingDocketEntry"
                ),
                "restrictedDocsAvailable": row.get("restrictedDocsAvailable"),
            }
            entries.append(entry_data)

        docket_info["docketEntries"] = entries
        return docket_info

    def _map_docket_entry_document(
        self, raw_doc_data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Maps a raw dictionary representing a docket entry document to a
        standardized format.


        :param raw_doc_data: A single dictionary object for a document.

        :return: A dictionary containing the mapped document details.
                Returns an empty dictionary if raw_doc_data is None or empty.
        """
        if not raw_doc_data:
            return {}

        return {
            "docketDocumentDetailsId": raw_doc_data.get(
                "acms_docketdocumentdetailsid"
            ),
            "name": raw_doc_data.get("acms_name"),
            "documentUrl": raw_doc_data.get("acms_documenturl"),
            "caseFilingDocumentUrl": raw_doc_data.get(
                "acms_casefilingdocumenturl"
            ),
            "documentPermission": raw_doc_data.get("acms_documentpermission"),
            "pageCount": raw_doc_data.get("acms_pagecount"),
            "fileSize": raw_doc_data.get("acms_filesize"),
            "createdOn": raw_doc_data.get("createdon"),
            "billablePages": raw_doc_data.get("billablePages"),
            "cost": raw_doc_data.get("cost"),
            "documentNumber": raw_doc_data.get("acms_documentnumber"),
            "searchValue": raw_doc_data.get("searchValue"),
            "searchTransaction": raw_doc_data.get("searchTransaction"),
        }

    def get_case_details(self, case_id: str) -> dict[str, Any]:
        """
        Fetches and maps case details for a given case ID.

        :param case_id: The unique identifier of the case.
        :return: The mapped case details.
        """
        path = self.CASE_DETAILS_ENDPOINT.format(case_id=case_id)
        url = f"{self.base_url}{path}"
        logger.info(f"Fetching case details from: {url}")
        response = self.session.get(url)
        response.raise_for_status()
        return self._map_case_details_response(response.json())

    def get_docket_entries(self, case_id: str) -> dict[str, Any]:
        """
        Fetches and maps docket entry details for a given case ID.

        :param case_id: The unique identifier of the case.
        :return: The mapped docket entry details.
        """
        path = self.DOCKET_ENTRIES_ENDPOINT.format(case_id=case_id)
        url = f"{self.base_url}{path}"
        logger.info(f"Fetching docket entries from: {url}")
        response = self.session.post(
            url,
            json={
                "csoId": self.session.acms_user_data["CsoId"],
                "contactType": self.session.acms_user_data["ContactType"],
            },
        )
        response.raise_for_status()
        return self._map_docket_entries_response(response.json())

    def get_attachments(
        self,
        docket_entry_id: str,
        is_case_participant: bool,
        is_restricted_party_filing_entry: bool,
    ) -> list[dict[str, Any]]:
        """
        Fetches and maps attachments for a specific docket entry.

        :param docket_entry_id: The ID of the docket entry to retrieve
                                attachments for.
        :param is_case_participant: Indicates if the user is a participant in
                                    the case.
        :param is_restricted_party_filing_entry: Indicates if the docket entry is a
                                                restricted party filing.
        :return: A list of dictionaries, where each dictionary represents an
                 attachment.
        """
        path = self.ATTACHMENTS_ENDPOINT.format(entry_id=docket_entry_id)
        url = f"{self.base_url}{path}"
        logger.info(f"Fetching attachment from: {url}")
        response = self.session.post(
            url,
            json={
                "isUserCaseParticipant": is_case_participant,
                "restrictedPartyFilingDocketEntry": is_restricted_party_filing_entry,
            },
        )
        response.raise_for_status()
        raw_attachments = response.json()
        if not raw_attachments:
            return []

        return [
            self._map_docket_entry_document(attachment)
            for attachment in raw_attachments
        ]
