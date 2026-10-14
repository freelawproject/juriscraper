import asyncio
import random
from collections.abc import Mapping
from datetime import datetime
from typing import TYPE_CHECKING

from httpx import Response
from pydantic import TypeAdapter

from juriscraper.lib.acms_types import (
    CASE_DETAILS,
    DOCKET_INFO,
    DOCUMENTS,
    MERGE_REQUEST,
    MERGE_STATUS,
    AcmsCaseDetails,
    AcmsDocketInfo,
    AcmsDocument,
)
from juriscraper.lib.log_tools import make_default_logger

if TYPE_CHECKING:
    from juriscraper.pacer.http import PacerSession

logger = make_default_logger()

_API_OBJECT = TypeAdapter(dict[str, object])
_API_OBJECTS = TypeAdapter(list[dict[str, object]])


async def add_delay(delay: int = 0, deviation: int = 0) -> None:
    """Create a semi-random delay.

    Delay is the number of seconds your program will be stopped for, and
    deviation is the number of seconds that the delay can vary.
    """
    from juriscraper.AbstractSite import logger

    duration = random.randrange(delay - deviation, delay + deviation)
    logger.info(f"Adding a delay of {duration} seconds. Please wait.")
    await asyncio.sleep(duration)


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
    MERGE_PDF_ENDPOINT = "MergePDFFiles/"
    GET_PDF_ENDPOINT = "GetMergedFile/"

    def __init__(self, session: "PacerSession | None", court_id: str) -> None:
        self.session = session
        self.court_id = court_id
        self.base_url = self.BASE_URL_TEMPLATE.format(court_id=self.court_id)

    def _map_case_details_response(
        self, raw_data: Mapping[str, object]
    ) -> AcmsCaseDetails:
        """
        Maps the raw API response for case details to a standardized dictionary
        format.

        This method extracts and renames specific fields relevant to existing
        logic for parties and metadata. Not all fields from the raw response are
        mapped.

        :param raw_data: The raw dictionary response from the case details API.
        :return: A dictionary containing the mapped case details.
        """
        raw_byte_count = raw_data.get("byteCount")
        if (
            raw_byte_count is None
            or raw_byte_count == ""
            or raw_byte_count == 0
        ):
            byte_count = None
        elif isinstance(raw_byte_count, str | int | float):
            byte_count = int(raw_byte_count)
        else:
            raise ValueError("ACMS byte count must be numeric")
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
            "byteCount": byte_count,
        }
        for name, key, field in (
            ("caseType", "pcx_casetype", "pcx_casetypename"),
            ("caseSubType", "pcx_casesubtype", "pcx_casesubtypename"),
            ("caseSubSubType", "pcx_casesubsubtype", "pcx_casesubsubtypename"),
            ("districtCourtName", "acms_DistrictCourt", "pcx_districtname"),
            ("feeStatus", "acms_feestatusid", "acms_feestatusname"),
            ("natureOfSuit", "acms_NatureofSuit", "acms_name"),
        ):
            value = raw_data.get(key)
            case_details[name] = (
                _API_OBJECT.validate_python(value, strict=True).get(field)
                if value is not None
                else None
            )

        if bool(raw_data.get("pcx_court")):
            court = _API_OBJECT.validate_python(
                raw_data["pcx_court"], strict=True
            )
            case_details["court"] = {
                "name": court.get("pcx_name"),
                "abbreviatedName": court.get("acms_abbreviatedname"),
            }

        return CASE_DETAILS.validate_python(case_details, strict=True)

    def _map_docket_entries_response(
        self, raw_data: Mapping[str, object]
    ) -> AcmsDocketInfo:
        """
        Maps the raw API response for docket entry details to a standardized
        format.

        :param raw_data: The raw dictionary response from the docket entries API
        :return: A dictionary containing the mapped data for entries.
        """
        raw_byte_count = raw_data.get("byteCount")
        if (
            raw_byte_count is None
            or raw_byte_count == ""
            or raw_byte_count == 0
        ):
            byte_count = None
        elif isinstance(raw_byte_count, str | int | float):
            byte_count = int(raw_byte_count)
        else:
            raise ValueError("ACMS byte count must be numeric")
        docket_info = {
            "isCaseSealed": raw_data.get("isCaseSealed"),
            "isUserCaseParticipant": raw_data.get("isUserCaseParticipant"),
            "byteCount": byte_count,
        }

        entries = []
        for row in _API_OBJECTS.validate_python(
            raw_data.get("matchingDocketEntries", []), strict=True
        ):
            end_date: object = row.get("pcx_enddate")
            if not isinstance(end_date, str):
                raise ValueError("An ACMS docket entry must have an end date.")
            entry_data = {
                "endDate": row.get("pcx_enddate"),
                "endDateFormatted": datetime.strptime(
                    end_date, "%Y-%m-%d"
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
        return DOCKET_INFO.validate_python(docket_info, strict=True)

    def _map_docket_entry_document(
        self, raw_doc_data: Mapping[str, object]
    ) -> dict[str, object]:
        """
        Maps a raw dictionary representing a docket entry document to a
        standardized format.


        :param raw_doc_data: A single dictionary object for a document.

        :return: A dictionary containing the mapped document details.
                Returns an empty dictionary if raw_doc_data is None or empty.
        """
        if not bool(raw_doc_data):
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

    async def get_case_details(self, case_id: str) -> AcmsCaseDetails:
        """
        Fetches and maps case details for a given case ID.

        :param case_id: The unique identifier of the case.
        :return: The mapped case details.
        """
        path = self.CASE_DETAILS_ENDPOINT.format(case_id=case_id)
        url = f"{self.base_url}{path}"
        logger.info(f"Fetching case details from: {url}")
        if self.session is None:
            raise ValueError("A PACER session is required for ACMS API calls.")
        response = await self.session.get(url)
        response.raise_for_status()
        return self._map_case_details_response(response.json())

    async def get_docket_entries(self, case_id: str) -> AcmsDocketInfo:
        """
        Fetches and maps docket entry details for a given case ID.

        :param case_id: The unique identifier of the case.
        :return: The mapped docket entry details.
        """
        path = self.DOCKET_ENTRIES_ENDPOINT.format(case_id=case_id)
        url = f"{self.base_url}{path}"
        logger.info(f"Fetching docket entries from: {url}")
        session = self.session
        if session is None:
            raise ValueError("A PACER session is required for ACMS API calls.")
        response = await session.post(
            url,
            json={
                "csoId": session.acms_user_data["CsoId"],
                "contactType": session.acms_user_data["ContactType"],
            },
        )
        response.raise_for_status()
        return self._map_docket_entries_response(response.json())

    async def get_attachments(
        self,
        docket_entry_id: str,
        is_case_participant: bool,
        is_restricted_party_filing_entry: bool,
    ) -> list[AcmsDocument]:
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
        if self.session is None:
            raise ValueError("A PACER session is required for ACMS API calls.")
        response = await self.session.post(
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

        documents = [
            self._map_docket_entry_document(attachment)
            for attachment in raw_attachments
        ]
        return DOCUMENTS.validate_python(documents, strict=True)

    async def download_pdf(
        self,
        document_id: str,
        page_count: int,
        document_url: str,
        max_attempts: int = 90,
        poll_interval: float = 1.0,
    ) -> Response:
        """
        Requests generation and download of a merged PDF from the remote API.

        This method sends a request to merge a document, polls the status
        of the operation until it is completed, and then retrieves the PDF file
        from the API.

        :param document_id: identifier of the document in the ACMS system.
        :param page_count: number of pages in the document.
        :param document_url: The URL where the source document can be accessed.
        :param max_attempts: Maximum number of polling attempts before timing out.
        :param poll_interval: Seconds to wait between polling attempts.
        :return: The HTTP response containing the merged PDF file.
        """
        # API endpoints for merge and retrieval
        merge_pdf_path = f"{self.base_url}{self.MERGE_PDF_ENDPOINT}"
        get_pdf_path = f"{self.base_url}{self.GET_PDF_ENDPOINT}"

        # Request body specifying the document to merge
        body = {
            "header": True,
            "mergeScope": "External",
            "pagination": False,
            "docketEntryDocuments": [
                {
                    "acms_docketdocumentdetailsid": document_id,
                    "acms_documenturl": document_url,
                    "acms_pagecount": page_count,
                }
            ],
        }
        # Step 1: Request PDF merge operation
        session = self.session
        if session is None:
            raise ValueError("A PACER session is required for ACMS API calls.")
        response = await session.post(merge_pdf_path, json=body)
        response.raise_for_status()
        data = MERGE_REQUEST.validate_json(response.content, strict=True)

        # Extract URL to check merge job status
        status_url = data["statusQueryGetUri"]

        # Step 2: Poll until the merge job is completed or timeout
        for _ in range(max_attempts):
            response = await session.get(status_url)
            response.raise_for_status()
            job = MERGE_STATUS.validate_json(response.content, strict=True)
            status = job["runtimeStatus"].lower()

            if status == "completed":
                pdf_id = job.get("output")
                if not bool(pdf_id):
                    raise ValueError(
                        "Completed ACMS merge job has no file ID."
                    )
                break

            await asyncio.sleep(poll_interval)
        else:
            # If loop completes without break
            raise TimeoutError(
                f"Merge job did not complete after {max_attempts} attempts."
            )

        # Step 3: Retrieve the merged PDF by its file ID
        response = await session.get(f"{get_pdf_path}?fileGuid={pdf_id}")
        response.raise_for_status()
        return response
