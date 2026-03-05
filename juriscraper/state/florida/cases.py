from datetime import datetime
from typing import ClassVar

from pydantic import UUID4, AliasPath, BaseModel, Field

from juriscraper.state.florida.api import FloridaPaginatedResults
from juriscraper.state.parser import LegacyParser


class FloridaOriginatingCase(BaseModel):
    court_name: str = Field(alias="originatingCourtName")
    case_number: str = Field(alias="originatingCourtCaseNumber")


class FloridaCase(BaseModel):
    uuid: UUID4 = Field(
        validation_alias=AliasPath("caseHeader", "caseInstanceUUID")
    )
    case_number: str = Field(
        validation_alias=AliasPath("caseHeader", "caseNumber")
    )
    case_title: str = Field(
        validation_alias=AliasPath("caseHeader", "caseTitle")
    )
    case_caption: str = Field(
        validation_alias=AliasPath("caseHeader", "caseCaption")
    )
    closed_flag: bool = Field(
        validation_alias=AliasPath("caseHeader", "closedFlag")
    )
    class_group_type: str = Field(
        validation_alias=AliasPath("caseHeader", "caseClassGroupType")
    )
    class_group_type_id: int = Field(
        validation_alias=AliasPath("caseHeader", "caseClassGroupTypeID")
    )
    classification: str = Field(
        validation_alias=AliasPath("caseHeader", "caseClassification")
    )
    classification_id: int = Field(
        validation_alias=AliasPath("caseHeader", "caseClassificationID")
    )
    court_id: int = Field(validation_alias=AliasPath("caseHeader", "courtID"))
    location: str = Field(validation_alias=AliasPath("caseHeader", "location"))
    location_id: int = Field(
        validation_alias=AliasPath("caseHeader", "locationID")
    )
    date_filed: datetime = Field(
        validation_alias=AliasPath("caseHeader", "filedDate")
    )
    case_group_flag: bool = Field(
        validation_alias=AliasPath("caseHeader", "caseGroupFlag")
    )
    panel_flag: bool = Field(
        validation_alias=AliasPath("caseHeader", "panelFlag")
    )
    originating_cases: list[FloridaOriginatingCase] = Field(
        validation_alias=AliasPath("caseHeader", "originatingCourtCases")
    )


class FloridaCaseListParser(LegacyParser[list[FloridaCase]]):
    endpoint: ClassVar[str] = "/courts/cms/cases/{case}"

    def validate(self, _output: list[FloridaCase]) -> bool:
        return True

    def _parse(self, i: str) -> list[FloridaCase]:
        results = FloridaPaginatedResults[FloridaCase].model_validate_json(i)
        return results.results


class FloridaCaseInfoParser(LegacyParser[FloridaCase]):
    endpoint: ClassVar[str] = "/courts/{court}/cms/cases/{case}"

    def _parse(self, i: str) -> FloridaCase:
        return FloridaCase.model_validate_json(i)
