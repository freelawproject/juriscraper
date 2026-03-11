from datetime import date, datetime
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

from juriscraper.abstract_parser import AbstractParser
from juriscraper.lib.string_utils import clean_string, harmonize
from juriscraper.state.docket import Docket, DocketTransfer, DocketType
from juriscraper.state.florida.common import (
    FloridaPaginatedResults,
    datetime_str_to_date_validator,
    florida_docket_number_validator,
)
from juriscraper.state.florida.docket_entries import FloridaDocketEntry
from juriscraper.state.florida.parties import FloridaParty

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
    """
    Validates and converts a Florida case classification string to a
    DocketType enum value.

    The classification string is expected in the format
    "Category - Type - SubType", where the type component is looked up in
    FLORIDA_DOCKET_TYPE_MAP.

    :param i: Florida case classification string.

    :return: The corresponding DocketType enum value.

    :raise PydanticCustomError: If the string does not have exactly three
        dash-separated parts or if the type is not in the map.
    """
    parts = [p.strip().lower() for p in i.split(" - ")]
    if len(parts) != 3:
        raise PydanticCustomError(
            "florida_docket_type",
            "Invalid Florida docket type format: {dt}",
            {"dt": i},
        )

    _case_category, case_type, _case_sub_type = parts

    if case_type not in FLORIDA_DOCKET_TYPE_MAP:
        raise PydanticCustomError(
            "florida_docket_type",
            "Unrecognized Florida docket type: {dt}",
            {"dt": i},
        )

    return FLORIDA_DOCKET_TYPE_MAP[case_type]


class FloridaOriginatingCase(BaseModel):
    """
    A lower court case from which a Florida appellate case originated.

    :ivar court_name: The name of the originating court.
    :ivar case_number: The case number in the originating court.
    """

    court_name: str = Field(validation_alias="originatingCourtName")
    case_number: str = Field(validation_alias="originatingCaseNumber")


class FloridaCase(Docket[DocketTransfer, FloridaDocketEntry, FloridaParty]):
    """
    Extension of the Docket data structure with Florida-specific fields.

    :ivar uuid: The UUID of this case for use in API requests.
    :ivar docket_number: The case number assigned by the court.
    :ivar case_name: The case title, cleaned and harmonized.
    :ivar case_name_full: The case title with minimal cleaning.
    :ivar case_caption: The case caption, if available.
    :ivar closed_flag: Whether this case is closed.
    :ivar class_group_type: The case class group type name.
    :ivar class_group_type_id: Florida internal integer ID of the case class
        group type.
    :ivar docket_type: The DocketType derived from the case classification.
    :ivar classification_id: Florida internal integer ID of the case
        classification.
    :ivar court_id: Florida internal ID of the court.
    :ivar location: The location name within the court.
    :ivar location_id: Florida internal integer ID of the location.
    :ivar date_filed: The date this case was filed.
    :ivar datetime_filed: The date and time this case was filed according to
        the API.
    :ivar case_group_flag: Whether this case is part of a case group.
    :ivar panel_flag: Whether a panel has been assigned to this case.
    :ivar originating_cases: Lower court cases from which this case originated.
    :ivar transfers: Transfers of this case between courts.
    :ivar entries: Docket entries filed in this case.
    :ivar parties: Parties in this case.
    """

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
    court_id: str = Field(validation_alias=AliasPath("caseHeader", "courtID"))
    location: str = Field(
        validation_alias=AliasPath("caseHeader", "location"), default=""
    )
    location_id: int = Field(
        validation_alias=AliasPath("caseHeader", "locationID"), default=0
    )
    date_filed: Annotated[
        date,
        BeforeValidator(
            datetime_str_to_date_validator, json_schema_input_type=str
        ),
    ] = Field(validation_alias=AliasPath("caseHeader", "filedDate"))
    datetime_filed: datetime = Field(
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


class FloridaCaseListParser(AbstractParser[list[FloridaCase]]):
    """
    Parser for Florida case list API results.

    :cvar endpoint: The API endpoint for fetching cases from a given court.
    """

    endpoint: ClassVar[str] = "/courts/cms/cases/{case}"

    def _parse(self, i: str) -> list[FloridaCase]:
        results = FloridaPaginatedResults[FloridaCase].model_validate_json(i)
        return results.results


class FloridaCaseInfoParser(AbstractParser[FloridaCase]):
    """
    Parser for Florida case info API results.

    :cvar endpoint: The API endpoint for fetching info about a specific case.
    """

    endpoint: ClassVar[str] = "/courts/{court}/cms/cases/{case}"

    def _parse(self, i: str) -> FloridaCase:
        return FloridaCase.model_validate_json(i)
