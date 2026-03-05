from datetime import datetime
from typing import Annotated, ClassVar

from pydantic import (
    UUID4,
    AfterValidator,
    AliasPath,
    BaseModel,
    BeforeValidator,
    Field,
)
from pydantic_core import PydanticCustomError

from juriscraper.lib.string_utils import clean_string, harmonize
from juriscraper.state.docket import Docket, DocketTransfer, DocketType
from juriscraper.state.florida.common import (
    FloridaPaginatedResults,
    florida_docket_number_validator,
)
from juriscraper.state.florida.docket_entries import FloridaDocketEntry
from juriscraper.state.florida.parties import FloridaParty
from juriscraper.state.parser import LegacyParser

# Values retrieved 2026-03-05
FLORIDA_DOCKET_TYPE_MAP: dict[str, DocketType] = {
    "notice of appeal": DocketType.UNKNOWN,
    "notice to invoke": DocketType.UNKNOWN,
    "death penalty appeal": DocketType.DEATH_APPEAL,
    "death penalty petition": DocketType.UNKNOWN,
    "death penalty writ": DocketType.UNKNOWN,
    "petition for review": DocketType.UNKNOWN,
    "administrative": DocketType.ADMINISTRATIVE,
    "circuit civil": DocketType.CIVIL,
    "circuit criminal": DocketType.CRIMINAL,
    "circuit family": DocketType.FAMILY,
    "circuit guardianship": DocketType.FAMILY,
    "circuit juvenile": DocketType.JUVENILE,
    "circuit probate": DocketType.PROBATE,
    "county administrative": DocketType.ADMINISTRATIVE,
    "county civil": DocketType.CIVIL,
    "county criminal misdemeanor": DocketType.CRIMINAL,
    "county criminal traffic": DocketType.CRIMINAL,
    "county family": DocketType.FAMILY,
    "county small claims": DocketType.UNKNOWN,
    "workers compensation": DocketType.UNKNOWN,
    "advisory opinion": DocketType.UNKNOWN,
    "county misdemeanor": DocketType.CRIMINAL,
    "florida bar": DocketType.UNKNOWN,
    "florida board of bar examiners": DocketType.UNKNOWN,
    "judicial qualifications commission (jqc)": DocketType.UNKNOWN,
    "rules": DocketType.UNKNOWN,
    "writ": DocketType.UNKNOWN,
}


def florida_docket_type_validator(i: str) -> DocketType:
    parts = [p.strip().lower() for p in i.split("-")]
    if len(parts) != 3:
        raise PydanticCustomError(
            "florida_docket_type",
            "Invalid Florida docket type format: {dt}",
            {"dt": i},
        )

    case_category, case_type, case_sub_type = parts

    if case_type not in FLORIDA_DOCKET_TYPE_MAP:
        raise PydanticCustomError(
            "florida_docket_type",
            "Unrecognized Florida docket type: {dt}",
            {"dt": i},
        )

    return FLORIDA_DOCKET_TYPE_MAP[case_type]


class FloridaOriginatingCase(BaseModel):
    court_name: str = Field(validation_alias="originatingCourtName")
    case_number: str = Field(validation_alias="originatingCaseNumber")


class FloridaCase(Docket[DocketTransfer, FloridaDocketEntry, FloridaParty]):
    uuid: UUID4 = Field(
        validation_alias=AliasPath("caseHeader", "caseInstanceUUID")
    )
    docket_number: Annotated[
        str, AfterValidator(florida_docket_number_validator)
    ] = Field(validation_alias=AliasPath("caseHeader", "caseNumber"))
    case_name: Annotated[str, AfterValidator(harmonize)] = Field(
        validation_alias=AliasPath("caseHeader", "caseTitle")
    )
    case_name_full: Annotated[str, AfterValidator(clean_string)] = Field(
        validation_alias=AliasPath("caseHeader", "caseTitle")
    )
    case_caption: Annotated[str, AfterValidator(clean_string)] = Field(
        validation_alias=AliasPath("caseHeader", "caseCaption"), default=""
    )
    closed_flag: bool = Field(
        validation_alias=AliasPath("caseHeader", "closedFlag")
    )
    class_group_type: str = Field(
        validation_alias=AliasPath("caseHeader", "caseClassGroupType"),
        default="",
    )
    class_group_type_id: int = Field(
        validation_alias=AliasPath("caseHeader", "caseClassGroupTypeID"),
        default=0,
    )
    docket_type: Annotated[
        DocketType,
        BeforeValidator(
            florida_docket_type_validator, json_schema_input_type=str
        ),
    ] = Field(validation_alias=AliasPath("caseHeader", "caseClassification"))
    classification_id: int = Field(
        validation_alias=AliasPath("caseHeader", "caseClassificationID")
    )
    court_id: int = Field(validation_alias=AliasPath("caseHeader", "courtID"))
    location: str = Field(
        validation_alias=AliasPath("caseHeader", "location"), default=""
    )
    location_id: int = Field(
        validation_alias=AliasPath("caseHeader", "locationID"), default=0
    )
    date_filed: datetime = Field(
        validation_alias=AliasPath("caseHeader", "filedDate")
    )
    case_group_flag: bool = Field(
        validation_alias=AliasPath("caseHeader", "caseGroupFlag"),
        default=False,
    )
    panel_flag: bool = Field(
        validation_alias=AliasPath("caseHeader", "panelFlag"), default=False
    )
    originating_cases: list[FloridaOriginatingCase] = Field(
        validation_alias=AliasPath("caseHeader", "originatingCourtCases")
    )
    transfers: list[DocketTransfer] = []
    entries: list[FloridaDocketEntry] = []
    parties: list[FloridaParty] = []


class FloridaCaseListParser(LegacyParser[list[FloridaCase]]):
    endpoint: ClassVar[str] = "/courts/cms/cases/{case}"

    def _parse(self, i: str) -> list[FloridaCase]:
        results = FloridaPaginatedResults[FloridaCase].model_validate_json(i)
        return results.results


class FloridaCaseInfoParser(LegacyParser[FloridaCase]):
    endpoint: ClassVar[str] = "/courts/{court}/cms/cases/{case}"

    def _parse(self, i: str) -> FloridaCase:
        return FloridaCase.model_validate_json(i)
