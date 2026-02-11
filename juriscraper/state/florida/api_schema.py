from typing import Generic, TypeAliasType, TypeVar

from pydantic import AliasPath, BaseModel, Field

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


FloridaCaseParties = TypeAliasType(
    "FloridaCaseParties", FloridaPaginatedResults[FloridaCaseParty]
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


FloridaDocketEntries = TypeAliasType(
    "FloridaDocketEntries", FloridaPaginatedResults[FloridaDocketEntry]
)


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
