from datetime import datetime
from typing import Annotated, Any, ClassVar

from pydantic import (
    UUID4,
    AliasPath,
    BaseModel,
    BeforeValidator,
    Field,
)
from pydantic_core import PydanticCustomError

from juriscraper.state.docket import DocketEntry, DocketEntryType
from juriscraper.state.florida.common import FloridaPaginatedResults
from juriscraper.state.florida.documents import FloridaDocument
from juriscraper.state.parser import LegacyParser

# Retrieved 2026-03-06
FLORIDA_DOCKET_ENTRY_TYPE_MAP: dict[str, DocketEntryType] = {
    "bar discipline (before a referee) (sc)": DocketEntryType.UNKNOWN,
    "brief": DocketEntryType.BRIEF,
    "disposition (sc)": DocketEntryType.DISPOSITION,
    "disposition by opinion": DocketEntryType.DISPOSITION,
    "disposition by order": DocketEntryType.DISPOSITION,
    "disposition by pca": DocketEntryType.DISPOSITION,
    "disposition by pcd": DocketEntryType.DISPOSITION,
    "event": DocketEntryType.EVENT,
    "fsc to ussc roa (sc)": DocketEntryType.UNKNOWN,
    "letter": DocketEntryType.LETTER,
    "letter-case (sc)": DocketEntryType.LETTER,
    "mandate": DocketEntryType.UNKNOWN,
    "mediation": DocketEntryType.UNKNOWN,
    "misc. events": DocketEntryType.EVENT,
    "miscellaneous document": DocketEntryType.UNKNOWN,
    "motion (sc)": DocketEntryType.MOTION,
    "motions extensions": DocketEntryType.MOTION,
    "motions other": DocketEntryType.MOTION,
    "motions relating to attorney fees/costs": DocketEntryType.MOTION,
    "motions relating to briefs": DocketEntryType.MOTION,
    "motions relating to oral argument": DocketEntryType.MOTION,
    "motions relating to parties and counsel": DocketEntryType.MOTION,
    "motions relating to records": DocketEntryType.MOTION,
    "notice": DocketEntryType.NOTICE,
    "opinion": DocketEntryType.UNKNOWN,
    "order": DocketEntryType.ORDER,
    "petition": DocketEntryType.PETITION,
    "post-disposition motions": DocketEntryType.MOTION,
    "post-disposition responses": DocketEntryType.UNKNOWN,
    "recognizing agreed extension": DocketEntryType.UNKNOWN,
    "record": DocketEntryType.UNKNOWN,
    "record sent to supreme court": DocketEntryType.UNKNOWN,
    "response": DocketEntryType.UNKNOWN,
    "supreme court": DocketEntryType.UNKNOWN,
    "tpr/dependency": DocketEntryType.UNKNOWN,
}


def florida_entry_type_validator(value: Any) -> DocketEntryType:
    s = str(value).lower()
    if s not in FLORIDA_DOCKET_ENTRY_TYPE_MAP:
        raise PydanticCustomError(
            "florida_docket_entry_type",
            "Unrecognized Florida docket entry type value: {type}.",
            {"type": s},
        )
    return FLORIDA_DOCKET_ENTRY_TYPE_MAP[s]


class FloridaCaseActor(BaseModel):
    display_name: str = Field(
        validation_alias=AliasPath("partyActorInstance", "displayName")
    )
    sort_name: str = Field(
        validation_alias=AliasPath("partyActorInstance", "sortName")
    )


class FloridaDocketEntry(DocketEntry[FloridaDocument]):
    uuid: UUID4 = Field(
        validation_alias=AliasPath("docketEntryHeader", "docketEntryUUID")
    )
    date_filed: datetime = Field(
        validation_alias=AliasPath("docketEntryHeader", "filedDate")
    )
    entry_type: Annotated[
        DocketEntryType,
        BeforeValidator(
            florida_entry_type_validator, json_schema_input_type=str
        ),
    ] = Field(
        validation_alias=AliasPath("docketEntryHeader", "docketEntryType"),
    )
    entry_type_raw: str = Field(
        validation_alias=AliasPath("docketEntryHeader", "docketEntryType"),
    )
    entry_type_id: int = Field(
        validation_alias=AliasPath("docketEntryHeader", "docketEntryTypeID")
    )
    entry_subtype: str = Field(
        validation_alias=AliasPath("docketEntryHeader", "docketEntrySubType")
    )
    entry_subtype_id: int = Field(
        validation_alias=AliasPath("docketEntryHeader", "docketEntrySubTypeID")
    )
    entry_name: str = Field(
        validation_alias=AliasPath("docketEntryHeader", "docketEntryName")
    )
    date_submitted: datetime = Field(
        validation_alias=AliasPath("docketEntryHeader", "submittedDate")
    )
    entry_status: str = Field(
        validation_alias=AliasPath("docketEntryHeader", "docketEntryStatus")
    )
    entry_status_id: int = Field(
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
    document_count: int = Field(
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
    submitted_by: list[FloridaCaseActor] = Field(
        validation_alias="submittedBy", default=[]
    )
    attachments: list[FloridaDocument] = []


class FloridaDocketEntryListParser(LegacyParser[list[FloridaDocketEntry]]):
    endpoint: ClassVar[str] = "/courts/{court}/cms/cases/{case}/docketentries"

    def _parse(self, i: str) -> list[FloridaDocketEntry]:
        results = FloridaPaginatedResults[
            FloridaDocketEntry
        ].model_validate_json(i)
        return results.results
