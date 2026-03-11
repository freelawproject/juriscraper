from datetime import date, datetime
from typing import Annotated, Any, ClassVar

from pydantic import (
    UUID4,
    AliasPath,
    BaseModel,
    BeforeValidator,
    Field,
)
from pydantic_core import PydanticCustomError

from juriscraper.abstract_parser import AbstractParser
from juriscraper.state.docket import DocketEntry, DocketEntryType
from juriscraper.state.florida.common import (
    FloridaPaginatedResults,
    datetime_str_to_date_validator,
)
from juriscraper.state.florida.documents import FloridaDocument

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
    """
    Validates and converts a Florida docket entry type string to a
    DocketEntryType enum value.

    :param value: The docket entry type string from the API response.

    :return: The corresponding DocketEntryType enum value.

    :raise PydanticCustomError: If the value is not in
        FLORIDA_DOCKET_ENTRY_TYPE_MAP.
    """
    s = str(value).lower()
    if s not in FLORIDA_DOCKET_ENTRY_TYPE_MAP:
        raise PydanticCustomError(
            "florida_docket_entry_type",
            "Unrecognized Florida docket entry type value: {type}.",
            {"type": s},
        )
    return FLORIDA_DOCKET_ENTRY_TYPE_MAP[s]


class FloridaCaseActor(BaseModel):
    """
    A party or actor associated with a docket entry submission.

    :ivar display_name: The display name of the actor.
    :ivar sort_name: The name used to sort this actor in lists.
    """

    display_name: str = Field(
        validation_alias=AliasPath("partyActorInstance", "displayName")
    )
    sort_name: str = Field(
        validation_alias=AliasPath("partyActorInstance", "sortName")
    )


class FloridaDocketEntry(DocketEntry[FloridaDocument]):
    """
    Extension of the DocketEntry data structure with Florida-specific fields.

    :ivar uuid: The UUID of this docket entry for use in API requests.
    :ivar date_filed: The date this entry was filed.
    :ivar datetime_filed: The date and time this entry was filed according to
        the Florida API.
    :ivar entry_type: The DocketEntryType derived from the entry type string.
    :ivar entry_type_raw: The entry type string as it appears in the API
        response.
    :ivar entry_type_id: Florida internal integer ID of the entry type.
    :ivar entry_subtype: The name of the entry subtype.
    :ivar entry_subtype_id: Florida internal integer ID of the entry subtype.
    :ivar entry_name: The name of the docket entry.
    :ivar date_submitted: The date this entry was submitted.
    :ivar entry_status: The status of this docket entry.
    :ivar entry_status_id: Florida internal integer ID of the entry status.
    :ivar entry_description: A description of the docket entry.
    :ivar official: Purpose unclear. Whether this is an official court entry?
    :ivar document_count: The number of documents attached to this entry.
    :ivar secured_document: Whether the documents are secured.
    :ivar security_1: Security flag 1.
    :ivar security_2: Security flag 2.
    :ivar security_3: Security flag 3.
    :ivar security_4: Security flag 4.
    :ivar security_5: Security flag 5.
    :ivar outcome_status: The outcome status of this docket entry (e.g.
        "Granted"). Only present for entries involving judicial determinations.
    :ivar outcome_status_id: Florida internal integer ID of the outcome
        status.
    :ivar composite_security: Unclear. Whether any security flags are active?
    :ivar submitted_by: The actors who submitted this entry.
    :ivar attachments: Documents attached to this entry.
    """

    uuid: UUID4 = Field(
        validation_alias=AliasPath("docketEntryHeader", "docketEntryUUID")
    )
    date_filed: Annotated[
        date,
        BeforeValidator(
            datetime_str_to_date_validator, json_schema_input_type=str
        ),
    ] = Field(validation_alias=AliasPath("docketEntryHeader", "filedDate"))
    datetime_filed: datetime = Field(
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
        validation_alias=AliasPath("docketEntryHeader", "documentCount"),
        default=0,
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
    outcome_status: str = Field(
        validation_alias=AliasPath("docketEntryHeader", "outcomeStatus"),
        default="",
    )
    outcome_status_id: int = Field(
        validation_alias=AliasPath("docketEntryHeader", "outcomeStatusID"),
        default=0,
    )
    composite_security: bool = Field(
        validation_alias=AliasPath("docketEntryHeader", "compositeSecurity")
    )
    submitted_by: list[FloridaCaseActor] = Field(
        validation_alias="submittedBy", default=[]
    )
    attachments: list[FloridaDocument] = []


class FloridaDocketEntryListParser(AbstractParser[list[FloridaDocketEntry]]):
    """
    Parser for Florida docket entry list API results.

    :cvar endpoint: The API endpoint for fetching a case's docket entries.
    """

    endpoint: ClassVar[str] = "/courts/{court}/cms/cases/{case}/docketentries"

    def _parse(self, i: str) -> list[FloridaDocketEntry]:
        results = FloridaPaginatedResults[
            FloridaDocketEntry
        ].model_validate_json(i)
        return results.results
