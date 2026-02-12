from typing import Generic, TypeVar

from pydantic import AliasPath, BaseModel, Field, validate_call

ResultType = TypeVar("ResultType")


class FloridaPaginatedResultsMeta(BaseModel):
    page_size: int = Field(alias="size")
    total_elements: int = Field(alias="totalElements")
    total_pages: int = Field(alias="totalPages")
    page_number: int = Field(alias="number")


class FloridaPaginatedResults(BaseModel, Generic[ResultType]):
    results: list[ResultType] = Field(
        validation_alias=AliasPath("_embedded", "results")
    )
    page: FloridaPaginatedResultsMeta


class FloridaPartyRepresentative(BaseModel):
    party_uuid: str = Field(
        validation_alias=AliasPath("attorneyPartyHeader", "casePartyUUID")
    )
    display_name: str = Field(
        validation_alias=AliasPath(
            "attorneyPartyHeader", "partyActorInstance", "displayName"
        )
    )
    sort_name: str = Field(
        validation_alias=AliasPath(
            "attorneyPartyHeader", "partyActorInstance", "sortName"
        )
    )
    primary_flag: bool = Field(alias="primaryFlag")


class FloridaCaseParty(BaseModel):
    uuid: str = Field(
        validation_alias=AliasPath("partyHeader", "casePartyUUID")
    )
    party_type: str = Field(
        validation_alias=AliasPath("partyHeader", "partyType")
    )
    party_type_id: str = Field(
        validation_alias=AliasPath("partyHeader", "partyTypeID")
    )
    party_subtype: str = Field(
        validation_alias=AliasPath("partyHeader", "partySubType")
    )
    party_subtype_id: str = Field(
        validation_alias=AliasPath("partyHeader", "partySubTypeID")
    )
    status: str = Field(
        validation_alias=AliasPath("partyHeader", "partyStatus")
    )
    status_id: str = Field(
        validation_alias=AliasPath("partyHeader", "partyStatusID")
    )
    display_name: str = Field(
        validation_alias=AliasPath(
            "partyHeader", "partyActorInstance", "displayName"
        )
    )
    sort_name: str = Field(
        validation_alias=AliasPath(
            "partyHeader", "partyActorInstance", "sortName"
        )
    )
    pro_se_flag: bool = Field(alias="proSeFlag")
    order_by: int = Field(alias="orderBy")
    representatives: list[FloridaPartyRepresentative] = Field(
        alias="legalRepresentations"
    )
    non_public_flag: bool = Field(alias="nonPublicFlag")
    party_number: int = Field(alias="partyNumber")
    involvement_type_id: str = Field(alias="involvementTypeID")


class FloridaCaseActor(BaseModel):
    display_name: str = Field(
        validation_alias=AliasPath("partyActorInstance", "displayName")
    )
    sort_name: str = Field(
        validation_alias=AliasPath("partyActorInstance", "sortName")
    )


class FloridaDocketEntry(BaseModel):
    uuid: str = Field(
        validation_alias=AliasPath("docketEntryHeader", "docketEntryUUID")
    )
    date_filed: str = Field(
        validation_alias=AliasPath("docketEntryHeader", "filedDate")
    )
    entry_type: str = Field(
        validation_alias=AliasPath("docketEntryHeader", "docketEntryType")
    )
    entry_type_id: str = Field(
        validation_alias=AliasPath("docketEntryHeader", "docketEntryTypeID")
    )
    entry_subtype: str = Field(
        validation_alias=AliasPath("docketEntryHeader", "docketEntrySubType")
    )
    entry_subtype_id: str = Field(
        validation_alias=AliasPath("docketEntryHeader", "docketEntrySubTypeID")
    )
    entry_name: str = Field(
        validation_alias=AliasPath("docketEntryHeader", "docketEntryName")
    )
    date_submitted: str = Field(
        validation_alias=AliasPath("docketEntryHeader", "submittedDate")
    )
    entry_status: str = Field(
        validation_alias=AliasPath("docketEntryHeader", "docketEntryStatus")
    )
    entry_status_id: str = Field(
        validation_alias=AliasPath("docketEntryHeader", "docketEntryStatusID")
    )
    entry_description: str = Field(
        validation_alias=AliasPath(
            "docketEntryHeader", "docketEntryDescription"
        )
    )
    official: bool = Field(
        validation_alias=AliasPath("docketEntryHeader", "official")
    )
    document_count: str = Field(
        validation_alias=AliasPath("docketEntryHeader", "documentCount")
    )
    secured_document: bool = Field(
        validation_alias=AliasPath("docketEntryHeader", "securedDocument")
    )
    security_1: bool = Field(
        validation_alias=AliasPath("docketEntryHeader", "security1")
    )
    security_2: bool = Field(
        validation_alias=AliasPath("docketEntryHeader", "security2")
    )
    security_3: bool = Field(
        validation_alias=AliasPath("docketEntryHeader", "security3")
    )
    security_4: bool = Field(
        validation_alias=AliasPath("docketEntryHeader", "security4")
    )
    security_5: bool = Field(
        validation_alias=AliasPath("docketEntryHeader", "security5")
    )
    composite_security: bool = Field(
        validation_alias=AliasPath("docketEntryHeader", "compositeSecurity")
    )
    submitted_by: list[FloridaCaseActor] = Field(alias="submittedBy")


class FloridaOriginatingCase(BaseModel):
    court_name: str = Field(alias="originatingCourtName")
    case_number: str = Field(alias="originatingCourtCaseNumber")


class FloridaCase(BaseModel):
    uuid: str = Field(
        validation_alias=AliasPath("caseHeader", "caseInstanceUUID")
    )
    case_number: str = Field(
        validation_alias=AliasPath("caseHeader", "caseInstanceUUID")
    )
    case_title: str = Field(
        validation_alias=AliasPath("caseHeader", "caseInstanceUUID")
    )
    case_caption: str = Field(
        validation_alias=AliasPath("caseHeader", "caseInstanceUUID")
    )
    closed_flag: bool = Field(
        validation_alias=AliasPath("caseHeader", "caseInstanceUUID")
    )
    class_group_type: str = Field(
        validation_alias=AliasPath("caseHeader", "caseInstanceUUID")
    )
    class_group_type_id: str = Field(
        validation_alias=AliasPath("caseHeader", "caseInstanceUUID")
    )
    classification: str = Field(
        validation_alias=AliasPath("caseHeader", "caseInstanceUUID")
    )
    classification_id: str = Field(
        validation_alias=AliasPath("caseHeader", "caseInstanceUUID")
    )
    court_id: str = Field(
        validation_alias=AliasPath("caseHeader", "caseInstanceUUID")
    )
    location: str = Field(
        validation_alias=AliasPath("caseHeader", "caseInstanceUUID")
    )
    location_id: str = Field(
        validation_alias=AliasPath("caseHeader", "caseInstanceUUID")
    )
    date_filed: str = Field(
        validation_alias=AliasPath("caseHeader", "caseInstanceUUID")
    )
    case_group_flag: bool = Field(
        validation_alias=AliasPath("caseHeader", "caseInstanceUUID")
    )
    panel_flag: bool = Field(
        validation_alias=AliasPath("caseHeader", "caseInstanceUUID")
    )
    originating_cases: list[FloridaOriginatingCase] = Field(
        alias="originatingCases"
    )


class FloridaCourtLocation(BaseModel):
    calendar_event_flag: bool = Field(alias="calendarEventFlag")
    case_location_flag: bool = Field(alias="caseLocationFlag")
    location_comment: str = Field(alias="locationComment")
    location_id: int = Field(alias="locationID")
    location_name: str = Field(alias="locationName")


class FloridaCourt(BaseModel):
    active: bool = Field(alias="active")
    display_name: bool = Field(alias="active")
    external_identifier: bool = Field(alias="active")
    modified_date: bool = Field(alias="active")
    modified_user_id: bool = Field(alias="active")
    note: bool = Field(alias="active")
    resource_id: bool = Field(alias="active")
    locations: list[FloridaCourtLocation]


class FloridaCasePartyType(BaseModel):
    id: int = Field(alias="participantTypeID")
    name: str = Field(alias="participantTypeName")
    comment: str = Field(alias="participantTypeComment")


class FloridaCaseInvolvementType(BaseModel):
    id: int = Field(alias="involvementTypeID")
    name: str = Field(alias="involvementTypeName")
    comment: str = Field(alias="involvementTypeComment")


class FloridaCasePartySubType(BaseModel):
    id: int = Field(alias="participantSubTypeID")
    name: str = Field(alias="participantSubTypeName")
    comment: str = Field(alias="participantSubTypeComment")
    party_type: FloridaCasePartyType = Field(alias="participantType")
    involvement_type: FloridaCaseInvolvementType = Field(
        alias="involvementType"
    )


class FloridaDocketEntryType(BaseModel):
    id: str = Field(alias="docketEntryTypeID")
    name: str = Field(alias="docketEntryTypeName")
    comment: str = Field(alias="docketEntryTypeComment")


class FloridaDocketEntrySubType(BaseModel):
    id: str = Field(alias="docketEntrySubTypeID")
    name: str = Field(alias="docketEntrySubTypeName")
    comment: str = Field(alias="docketEntrySubTypeComment")
    docket_entry_type: FloridaDocketEntryType = Field(alias="docketEntryType")


class FloridaCaseCategory(BaseModel):
    id: str = Field(alias="caseCategoryID")
    name: str = Field(alias="caseCategoryName")
    comment: str = Field(alias="caseCategoryComment")


class FloridaDocument(BaseModel):
    docket_entry_uuid: str = Field(alias="docketEntryUUID")
    document_link_uuid: str = Field(alias="documentLinkUUID")
    document_name: str = Field(alias="documentName")
    user_document_state: str = Field(alias="userDocumentState")
    case_uuid: str = Field(
        validation_alias=AliasPath("caseHeader", "caseInstanceUUID")
    )
    case_number: str = Field(
        validation_alias=AliasPath("caseHeader", "caseNumber")
    )
    case_title: str = Field(
        validation_alias=AliasPath("caseHeader", "caseTitle")
    )
    court_id: str = Field(validation_alias=AliasPath("caseHeader", "courtID"))
    document_type: str = Field(
        validation_alias=AliasPath("documentInfo", "documentType")
    )
    content_type: str = Field(
        validation_alias=AliasPath("documentInfo", "contentType")
    )
    file_extension: str = Field(
        validation_alias=AliasPath("documentInfo", "fileExtension")
    )
    page_count: str = Field(
        validation_alias=AliasPath("documentInfo", "pageCount")
    )
    file_size: str = Field(
        validation_alias=AliasPath("documentInfo", "fileSize")
    )


EndpointParameters = TypeVar("EndpointParameters")
EndpointReturn = TypeVar("EndpointReturn")


class Endpoint(Generic[EndpointParameters, EndpointReturn]):
    url: str

    def __init__(self, url: str):
        self.url = url

    @validate_call
    def request(self, **kwargs: EndpointParameters) -> EndpointReturn:
        _url = self.url.format(**kwargs)
        raise NotImplementedError()


florida_courts = Endpoint[None, FloridaPaginatedResults[FloridaCourt]](
    "/courts"
)

florida_case_party_sub_types = Endpoint[None, FloridaCasePartySubType](
    "/courts/casepartysubtypes"
)

florida_cases = Endpoint[None, FloridaPaginatedResults[FloridaCase]](
    "/courst/cms/cases"
)

florida_docket_entry_document_access = Endpoint[
    None, FloridaPaginatedResults[FloridaDocument]
]("/courts/cms/docketentrydocumentaccess")


class FloridaCourtParameter(BaseModel):
    court: str


florida_court_case_categories = Endpoint[
    FloridaCourtParameter, FloridaCaseCategory
]("/courts/{court}/cms/casecategories")

florida_court_docket_entry_sub_types = Endpoint[
    FloridaCourtParameter, FloridaDocketEntrySubType
]("/courts/{court}/docketentrysubtypes")


class FloridaCourtCaseParameter(FloridaCourtParameter):
    case: str


florida_court_case_info = Endpoint[FloridaCourtCaseParameter, FloridaCase](
    "/courts/{court}/cms/cases/{case}"
)

florida_court_case_parties = Endpoint[
    FloridaCourtCaseParameter, FloridaPaginatedResults[FloridaCaseParty]
]("/courts/{court}/cms/cases/{case}/parties")

florida_court_case_docket_entries = Endpoint[
    FloridaCourtCaseParameter, FloridaPaginatedResults[FloridaDocketEntry]
]("/courts/{court}/cms/cases/{case}/docketentries")
