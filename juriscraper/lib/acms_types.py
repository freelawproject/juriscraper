"""Validated payloads shared by the ACMS API client and report parsers."""

from typing import NotRequired

from pydantic import TypeAdapter
from typing_extensions import TypedDict


class AcmsCaseReference(TypedDict):
    caseId: str


class AcmsCourt(TypedDict, total=False):
    name: str | None
    abbreviatedName: str | None
    identifier: str | None


class AcmsCaseDetails(AcmsCaseReference):
    caseNumber: str
    name: str
    caseOpened: str
    partyAttorneyList: str
    court: NotRequired[AcmsCourt | None]
    caseType: str | None
    caseSubType: str | None
    caseSubSubType: str | None
    districtCourtName: str | None
    feeStatus: str | None
    aNumber: str | None
    originatingCaseNumber: NotRequired[str | None]
    caseFormType: NotRequired[str | None]
    receivedDate: NotRequired[str | None]
    decisionDate: NotRequired[str | None]
    shortCaption: NotRequired[str | None]
    byteCount: NotRequired[int | None]
    natureOfSuit: NotRequired[str | None]


class AcmsAttachmentEntry(TypedDict):
    endDate: str
    entryNumber: int
    docketEntryText: str
    docketEntryId: str
    createdOn: NotRequired[str | None]


class AcmsDocketEntry(TypedDict):
    endDate: NotRequired[str | None]
    endDateFormatted: str
    entryNumber: int
    docketEntryText: str
    docketEntryId: str
    createdOn: NotRequired[str | None]
    pageCount: int
    documentCount: NotRequired[int | None]
    fileSize: NotRequired[int | None]
    restrictedPartyFilingDocketEntry: NotRequired[bool | None]
    restrictedDocsAvailable: NotRequired[bool | None]


class AcmsDocketInfo(TypedDict):
    docketEntries: list[AcmsDocketEntry]
    isCaseSealed: NotRequired[bool | None]
    isUserCaseParticipant: NotRequired[bool | None]
    byteCount: NotRequired[int | None]


class AcmsDocument(TypedDict):
    docketDocumentDetailsId: str
    name: str
    documentUrl: NotRequired[str | None]
    documentPermission: str | None
    pageCount: NotRequired[int | None]
    fileSize: int | None
    createdOn: str
    billablePages: int | None
    cost: float | None
    documentNumber: str
    caseFilingDocumentUrl: NotRequired[str | None]
    searchValue: NotRequired[str | None]
    searchTransaction: NotRequired[str | None]


class AcmsDocketPayload(TypedDict):
    caseDetails: AcmsCaseDetails
    docketInfo: AcmsDocketInfo


class AcmsAttachmentPayload(TypedDict):
    caseDetails: AcmsCaseReference
    docketEntry: AcmsAttachmentEntry
    docketEntryDocuments: list[AcmsDocument]


class AcmsMergeRequest(TypedDict):
    statusQueryGetUri: str


class AcmsMergeStatus(TypedDict):
    runtimeStatus: str
    output: NotRequired[str | None]


CASE_DETAILS = TypeAdapter(AcmsCaseDetails)
DOCKET_INFO = TypeAdapter(AcmsDocketInfo)
DOCUMENT = TypeAdapter(AcmsDocument)
DOCUMENTS = TypeAdapter(list[AcmsDocument])
DOCKET_PAYLOAD = TypeAdapter(AcmsDocketPayload)
ATTACHMENT_PAYLOAD = TypeAdapter(AcmsAttachmentPayload)
MERGE_REQUEST = TypeAdapter(AcmsMergeRequest)
MERGE_STATUS = TypeAdapter(AcmsMergeStatus)
