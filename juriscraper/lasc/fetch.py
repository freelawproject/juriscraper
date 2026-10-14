from datetime import date, datetime
from typing import Generic, NotRequired, TypeAlias

import httpx
from pydantic import TypeAdapter
from typing_extensions import TypedDict, TypeVar

from juriscraper.lasc.http import LASCSession
from juriscraper.lib.log_tools import make_default_logger
from juriscraper.lib.utils import clean_court_object

logger = make_default_logger()

LASCValue: TypeAlias = str | int | float | bool | datetime | date | None
LASCRecord: TypeAlias = dict[str, LASCValue]
LASCDocket: TypeAlias = dict[str, LASCRecord | list[LASCRecord]]
_Session = TypeVar(
    "_Session", bound=LASCSession | None, default=LASCSession | None
)


class _CaseInformation(TypedDict):
    FilingDate: LASCValue
    CaseNumber: LASCValue
    District: LASCValue
    DivisionCode: LASCValue
    DispositionType: LASCValue
    CaseTypeDescription: LASCValue
    CaseType: LASCValue
    CaseTitle: LASCValue
    JudicialOfficer: LASCValue
    Courthouse: LASCValue
    StatusDate: LASCValue
    StatusCode: LASCValue
    Status: LASCValue
    CaseID: NotRequired[LASCValue]


class _Action(TypedDict):
    RegisterOfActionDate: LASCValue
    Description: LASCValue
    AdditionalInformation: LASCValue


class _CrossReference(TypedDict):
    CrossReferenceDate: LASCValue
    CrossReferenceCaseNumber: LASCValue
    CrossReferenceTypeDescription: LASCValue


class _DocumentFiled(TypedDict):
    DateFiled: LASCValue
    Memo: LASCValue
    Document: LASCValue
    Party: LASCValue


class _DocumentImage(TypedDict):
    createDate: LASCValue
    docFilingDate: LASCValue
    docId: LASCValue
    pageCount: LASCValue
    documentType: LASCValue
    documentTypeID: LASCValue
    imageTypeId: LASCValue
    appId: LASCValue
    OdysseyID: LASCValue
    IsDownloadable: LASCValue
    securityLevel: LASCValue
    description: LASCValue
    docPart: LASCValue


class _Party(TypedDict):
    AttorneyName: LASCValue
    AttorneyFirm: LASCValue
    EntityNumber: LASCValue
    Name: LASCValue
    PartyFlag: LASCValue
    PartyTypeCode: LASCValue
    PartyDescription: LASCValue


class _Proceeding(TypedDict):
    ProceedingDate: LASCValue
    ProceedingTime: LASCValue
    ProceedingRoom: LASCValue
    AMPM: LASCValue
    Memo: LASCValue
    CourthouseName: LASCValue
    Address: LASCValue
    Result: LASCValue
    Judge: LASCValue
    Event: LASCValue


class _TentativeRuling(TypedDict):
    CreationDate: LASCValue
    HearingDate: LASCValue
    Department: LASCValue
    Ruling: LASCValue


class _CaseData(TypedDict):
    CaseInformation: _CaseInformation
    RegisterOfActions: list[_Action]
    CrossReferences: list[_CrossReference]
    DocumentsFiled: list[_DocumentFiled]
    DocumentImages: list[_DocumentImage]
    Parties: list[_Party]
    PastProceedings: list[_Proceeding]
    FutureProceedings: list[_Proceeding]
    TentativeRulings: list[_TentativeRuling]


class _CaseResult(TypedDict):
    NonCriminalCaseInformation: _CaseData


class _CaseResponse(TypedDict):
    ResultList: list[_CaseResult]


class _SearchResult(TypedDict):
    InternalCaseID: LASCValue
    JudgeCode: LASCValue
    CaseTypeCode: LASCValue


class _SearchResponse(TypedDict):
    ResultList: list[_SearchResult]


_CASE_RESPONSE = TypeAdapter(_CaseResponse)
_SEARCH_RESPONSE = TypeAdapter(_SearchResponse)


class LASCSearch(Generic[_Session]):
    """
    An object designed to search the LA Superior Court Media Access Portal
    (MAP). It searches by date, looks up individual cases, and collects PDFs on
    those cases if made available in the MAP.
    """

    def __init__(self, session: _Session) -> None:
        self.session = session
        self.case_data: str | None = None
        self.api_base = "media.lacourt.org/api/AzureApi/"

    async def get_json_from_internal_case_id(
        self, internal_case_id: str
    ) -> LASCDocket:
        """Query LASC for the case json based on the internal case id

        :param internal_case_id: An internal ID of the form, 19STCV25157;SS;CV
        :return: The parsed docket data for the case requested
        """
        session: LASCSession | None = self.session
        if session is None:
            raise ValueError("A LASC session is required to query a case")
        r = await session.get(
            f"https://{self.api_base}GetCaseDetail/{internal_case_id}"
        )
        self._check_success(r)

        return self._parse_case_data(r.json())

    async def query_cases_by_date(
        self, start: date, end: date
    ) -> list[LASCRecord]:
        """Query LASC for a list of cases between two dates (inclusive)

        The LASC interface only allows queries of up to seven days at a time.
        If a wider request is made, break it into multiple smaller requests
        and append their results together.

        :param start: A date object to start the query
        :param end: A date object to end the query
        :return: A list of case metadata objects
        """
        start_str = start.strftime("%m-%d-%Y")
        end_str = end.strftime("%m-%d-%Y")
        date_query_url = (
            f"https://{self.api_base}GetRecentCivilCases/{start_str}/{end_str}"
        )
        session: LASCSession | None = self.session
        if session is None:
            raise ValueError("A LASC session is required to search cases")
        r = await session.get(date_query_url)
        r.raise_for_status()
        cases = _SEARCH_RESPONSE.validate_json(r.content, strict=True)[
            "ResultList"
        ]

        # Normalize the date data
        normal_cases: list[LASCRecord] = []
        for case in cases:
            clean_case: LASCRecord = {
                "internal_case_id": case["InternalCaseID"],
                "judge_code": (
                    case["JudgeCode"] if bool(case["JudgeCode"]) else ""
                ),
                "case_type_code": (
                    case["CaseTypeCode"] if bool(case["CaseTypeCode"]) else ""
                ),
            }
            normal_cases.append(clean_case)

        return normal_cases

    async def get_pdf_from_url(self, pdf_url: str) -> bytes:
        """Get a PDF from the MAP

        :param pdf_url: The URL to a particular PDF you wish to download
        :return: The binary PDF data
        """

        logger.info("Api ViewDocument called.  Downloading PDF ")
        session: LASCSession | None = self.session
        if session is None:
            raise ValueError("A LASC session is required to download a PDF")
        return (await session.get(pdf_url)).content

    @staticmethod
    def _parse_case_data(case_data: object) -> LASCDocket:
        """
        This function normalizes the json docket data we get from LA MAP

        The MAP, mercifully, gives us JSON data, so this isn't too bad. The
        main task, then, is to convert the various field names it provides over
        to field names following our conventions.

        :param case_data: A python dict of a docket as gathered from the MAP
        (this will be JSON data in the MAP, but convert it to Python before
        calling this method.)
        :return: The parsed, cleaned, normalized data
        """
        logger.info(
            "Parsing lasc data from returned JSON into normalized format"
        )

        payload = _CASE_RESPONSE.validate_python(case_data, strict=True)
        try:
            data = payload["ResultList"][0]["NonCriminalCaseInformation"]
        except IndexError:
            # Some cases don't have any data at all, see: P4160;JCC;CV. When
            # this happens, Juriscraper returns nothing as well.
            return {}

        # Docket Normalization
        clean_data: LASCDocket = {
            "QueuedCase": [],
            "LASCPDF": [],
            "LASCJSON": [],
        }

        case_info = data["CaseInformation"]
        filing_date = case_info["FilingDate"]
        if isinstance(filing_date, str):
            filing_date = datetime.fromisoformat(
                filing_date.replace("Z", "+00:00")
            )
        if isinstance(filing_date, datetime):
            filing_date = filing_date.date()
        if not isinstance(filing_date, date):
            raise ValueError("Case filing date is missing or invalid")

        docket: LASCRecord = {
            "date_filed": filing_date,
            "date_disposition": None,
            "docket_number": case_info["CaseNumber"],
            "district": case_info["District"],
            "division_code": case_info["DivisionCode"],
            "disposition_type": case_info["DispositionType"],
            "disposition_type_code": "",
            "case_type_str": case_info["CaseTypeDescription"],
            "case_type_code": case_info["CaseType"],
            "case_name": (
                case_info["CaseTitle"] if bool(case_info["CaseTitle"]) else ""
            ),
            "judge_code": "",
            "judge_name": case_info["JudicialOfficer"],
            "courthouse_name": case_info["Courthouse"],
        }

        status_date = case_info["StatusDate"]
        if isinstance(status_date, str):
            docket["date_status"] = datetime.strptime(
                status_date, "%m/%d/%Y"
            ).date()
        elif status_date is None or isinstance(status_date, date):
            docket["date_status"] = status_date
        else:
            raise ValueError("Case status date is invalid")

        docket["status_code"] = (
            case_info["StatusCode"] if bool(case_info["StatusCode"]) else ""
        )
        docket["status_str"] = case_info["Status"]
        clean_data["Docket"] = docket

        # Register of Actions normalization
        actions: list[LASCRecord] = []
        clean_data["Action"] = actions
        for action in data["RegisterOfActions"]:
            registered_action = {
                "date_of_action": action["RegisterOfActionDate"],
                "description": action["Description"],
                "additional_information": action["AdditionalInformation"],
            }
            actions.append(registered_action)

        # Cross References normalization
        cross_references: list[LASCRecord] = []
        clean_data["CrossReference"] = cross_references
        for cross_ref in data["CrossReferences"]:
            cross_reference = {
                "date_cross_reference": cross_ref["CrossReferenceDate"],
                "cross_reference_docket_number": (
                    cross_ref["CrossReferenceCaseNumber"]
                    if bool(cross_ref["CrossReferenceCaseNumber"])
                    else ""
                ),
                "cross_reference_type": cross_ref[
                    "CrossReferenceTypeDescription"
                ],
            }
            cross_references.append(cross_reference)

        # Documents Filed
        documents: list[LASCRecord] = []
        clean_data["DocumentFiled"] = documents
        for doc_filed in data["DocumentsFiled"]:
            document = {
                "date_filed": doc_filed["DateFiled"],
                "memo": (doc_filed["Memo"] if bool(doc_filed["Memo"]) else ""),
                "document_type": (
                    doc_filed["Document"]
                    if bool(doc_filed["Document"])
                    else ""
                ),
                "party_str": (
                    doc_filed["Party"] if bool(doc_filed["Party"]) else ""
                ),
            }
            documents.append(document)

        queued_pdfs: list[LASCRecord] = []
        document_images: list[LASCRecord] = []
        clean_data["QueuedPDF"] = queued_pdfs
        clean_data["DocumentImage"] = document_images
        for doc_image in data["DocumentImages"]:
            image = {
                "date_processed": doc_image["createDate"],
                "date_filed": doc_image["docFilingDate"],
                "doc_id": doc_image["docId"],
                "page_count": doc_image["pageCount"],
                "document_type": (
                    doc_image["documentType"]
                    if bool(doc_image["documentType"])
                    else ""
                ),
                "document_type_code": doc_image["documentTypeID"],
                "image_type_id": doc_image["imageTypeId"],
                "app_id": (
                    doc_image["appId"] if bool(doc_image["appId"]) else ""
                ),
                "odyssey_id": (
                    doc_image["OdysseyID"]
                    if bool(doc_image["OdysseyID"])
                    else ""
                ),
                "is_downloadable": doc_image["IsDownloadable"],
                "security_level": doc_image["securityLevel"],
                "description": (
                    doc_image["description"]
                    if bool(doc_image["description"])
                    else ""
                ),
                "doc_part": (
                    doc_image["docPart"] if bool(doc_image["docPart"]) else ""
                ),
                "is_available": False,
            }

            if "CaseID" not in case_info:
                raise KeyError("CaseID")
            pdf_queue = {
                "internal_case_id": case_info["CaseID"],
                "document_id": doc_image["docId"],
            }

            document_images.append(image)
            queued_pdfs.append(pdf_queue)

        parties: list[LASCRecord] = []
        clean_data["Party"] = parties
        for party in data["Parties"]:
            party_obj = {
                "attorney_name": party["AttorneyName"],
                "attorney_firm": party["AttorneyFirm"],
                "entity_number": party["EntityNumber"],
                "party_name": party["Name"],
                "party_flag": party["PartyFlag"],
                "party_type_code": (
                    party["PartyTypeCode"]
                    if bool(party["PartyTypeCode"])
                    else ""
                ),
                "party_description": (
                    party["PartyDescription"]
                    if bool(party["PartyDescription"])
                    else ""
                ),
            }
            parties.append(party_obj)

        proceedings: list[LASCRecord] = []
        clean_data["Proceeding"] = proceedings
        for proceeding in data["PastProceedings"]:
            event = {
                "past_or_future": 1,
                "date_proceeding": proceeding["ProceedingDate"],
                "proceeding_time": proceeding["ProceedingTime"],
                "proceeding_room": proceeding["ProceedingRoom"],
                "am_pm": proceeding["AMPM"],
                "memo": proceeding["Memo"],
                "courthouse_name": proceeding["CourthouseName"],
                "address": proceeding["Address"],
                "result": proceeding["Result"],
                "judge_name": proceeding["Judge"],
                "event": proceeding["Event"],
            }
            proceedings.append(event)

        for proceeding in data["FutureProceedings"]:
            event = {
                "past_or_future": 2,
                "date_proceeding": proceeding["ProceedingDate"],
                "proceeding_time": proceeding["ProceedingTime"],
                "proceeding_room": proceeding["ProceedingRoom"],
                "am_pm": proceeding["AMPM"],
                "memo": proceeding["Memo"],
                "courthouse_name": proceeding["CourthouseName"],
                "address": proceeding["Address"],
                "result": proceeding["Result"],
                "judge_name": proceeding["Judge"],
                "event": proceeding["Event"],
            }
            proceedings.append(event)

        tentative_rulings: list[LASCRecord] = []
        clean_data["TentativeRuling"] = tentative_rulings
        for ruling in data["TentativeRulings"]:
            tentative_ruling = {
                "date_created": ruling["CreationDate"],
                "date_hearing": ruling["HearingDate"],
                "department": ruling["Department"],
                "ruling": ruling["Ruling"],
            }

            tentative_rulings.append(tentative_ruling)

        clean_data = clean_court_object(clean_data)

        return clean_data

    def _check_success(self, r: httpx.Response) -> None:
        self.case_data = None
        payload: object = r.json()
        if not isinstance(payload, dict):
            raise ValueError("LASC response must be an object")
        if bool(payload.get("IsSuccess")):
            self.case_data = r.text
            logger.info("Successful query into LASC map")
        else:
            logger.info("Failure to query into LASC map")
