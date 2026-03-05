from datetime import datetime
from typing import Annotated, ClassVar

from pydantic import UUID4, AfterValidator, AliasPath, BaseModel, Field

from juriscraper.state.docket import Docket, DocketTransfer, DocketType
from juriscraper.state.florida.common import (
    FloridaPaginatedResults,
    florida_docket_number_validator,
)
from juriscraper.state.florida.docket_entries import FloridaDocketEntry
from juriscraper.state.florida.parties import FloridaParty
from juriscraper.state.parser import LegacyParser


class FloridaOriginatingCase(BaseModel):
    court_name: str = Field(alias="originatingCourtName")
    case_number: str = Field(alias="originatingCaseNumber")


class FloridaCase(Docket[DocketTransfer, FloridaDocketEntry, FloridaParty]):
    uuid: UUID4 = Field(
        validation_alias=AliasPath("caseHeader", "caseInstanceUUID")
    )
    docket_number: Annotated[
        str, AfterValidator(florida_docket_number_validator)
    ] = Field(validation_alias=AliasPath("caseHeader", "caseNumber"))
    case_name: str = Field(
        validation_alias=AliasPath("caseHeader", "caseTitle")
    )
    case_name_full: str = ""
    case_caption: str = Field(
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
    classification: str = Field(
        validation_alias=AliasPath("caseHeader", "caseClassification")
    )
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
    docket_type: DocketType = DocketType.UNKNOWN


class FloridaCaseListParser(LegacyParser[list[FloridaCase]]):
    endpoint: ClassVar[str] = "/courts/cms/cases/{case}"

    def _parse(self, i: str) -> list[FloridaCase]:
        results = FloridaPaginatedResults[FloridaCase].model_validate_json(i)
        return results.results


class FloridaCaseInfoParser(LegacyParser[FloridaCase]):
    endpoint: ClassVar[str] = "/courts/{court}/cms/cases/{case}"

    def _parse(self, i: str) -> FloridaCase:
        return FloridaCase.model_validate_json(i)
