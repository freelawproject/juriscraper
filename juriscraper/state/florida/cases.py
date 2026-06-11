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
from typing_extensions import override

from juriscraper.abstract_parser import LegacyParser
from juriscraper.lib.string_utils import clean_string, harmonize
from juriscraper.state.docket import (
    Docket,
    DocketTransfer,
    DocketType,
    TransferDirection,
    TransferReason,
)
from juriscraper.state.florida.arguments import FloridaArgument
from juriscraper.state.florida.common import (
    FloridaPaginatedResults,
    FloridaPaginatedResultsParser,
    datetime_str_to_date_validator,
    florida_docket_number_validator,
)
from juriscraper.state.florida.courts import (
    FLORIDA_COURT_EXTERNAL_ID_MAP,
    FloridaCourtID,
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
    if len(parts) < 3:
        raise PydanticCustomError(
            "florida_docket_type",
            "Invalid Florida docket type format: {dt}",
            {"dt": i},
        )

    _case_category, case_type, _case_sub_type = parts[:3]

    if case_type not in FLORIDA_DOCKET_TYPE_MAP:
        raise PydanticCustomError(
            "florida_docket_type",
            "Unrecognized Florida docket type: {dt}",
            {"dt": i},
        )

    return FLORIDA_DOCKET_TYPE_MAP[case_type]


def florida_originating_court_id_validator(i: str) -> FloridaCourtID:
    """
    Validates and converts a Florida originating court name to a standardized
    Florida court ID.

    :param i: Florida originating court name.

    :return: The corresponding CourtID enum value.

    :raise PydanticCustomError: If the court name is not recognized.
    """
    court_name = i.lower().strip()
    if court_name.startswith("circuit court"):
        return FloridaCourtID.CIRCUIT
    if court_name.startswith("county court"):
        return FloridaCourtID.COUNTY
    match court_name:
        case "administrative agency":
            return FloridaCourtID.ADMINISTRATIVE_AGENCY
        case "office of the judges of compensation claims":
            return FloridaCourtID.COMPENSATION_CLAIMS
        case "1st district court of appeal":
            return FloridaCourtID.FIRST_COA
        case "2nd district court of appeal":
            return FloridaCourtID.SECOND_COA
        case "3rd district court of appeal":
            return FloridaCourtID.THIRD_COA
        case "4th district court of appeal":
            return FloridaCourtID.FOURTH_COA
        case "5th district court of appeal":
            return FloridaCourtID.FIFTH_COA
        case "6th district court of appeal":
            return FloridaCourtID.SIXTH_COA
    raise PydanticCustomError(
        "florida_court_name",
        "Unrecognized Florida court name: {cn}",
        {"cn": i},
    )


class FloridaOriginatingCase(BaseModel):
    """
    A lower court case from which a Florida appellate case originated.

    :ivar court_name: The name of the originating court.
    :ivar court_id: Juriscraper court identifier. Will be aggregated in most
        cases due to the impracticality of creating an enum entry for every
        circuit and county court.
    :ivar case_number: The case number in the originating court.
    """

    court_name: str = Field(validation_alias="originatingCourtName")
    court_id: Annotated[
        FloridaCourtID,
        BeforeValidator(
            florida_originating_court_id_validator, json_schema_input_type=str
        ),
    ] = Field(validation_alias="originatingCourtName")
    case_number: str = Field(validation_alias="originatingCaseNumber")


def florida_external_id_to_js_id_validator(i: str) -> str:
    """
    Maps Florida's external court ID to a value on the FloridaCourtID enum.

    :param i: Florida external court ID as a string.

    :return: Value on the FloridaCourtID enum.

    :raise PydanticCustomError: If the court ID is not recognized.
    """
    if i not in FLORIDA_COURT_EXTERNAL_ID_MAP:
        raise PydanticCustomError(
            "florida_court_id",
            "Unrecognized Florida court ID: {id}",
            {"id": i},
        )
    return FLORIDA_COURT_EXTERNAL_ID_MAP[i].value


class FloridaCase(Docket[DocketTransfer, FloridaDocketEntry, FloridaParty]):
    """
    Extension of the Docket data structure with Florida-specific fields.

    :ivar case_uuid: The UUID of this case for use in API requests.
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
    :ivar court_id: Juriscraper court ID.
    :ivar court_abbreviation: The Florida abbreviation for the court (e.g.
        "1DCA").
    :ivar location: The location name within the court.
    :ivar location_id: Florida internal integer ID of the location.
    :ivar date_filed: The date this case was filed.
    :ivar datetime_filed: The date and time this case was filed according to
        the API.
    :ivar case_group_flag: Whether this case is part of a case group. ``None``
        if the API did not return a value.
    :ivar panel_flag: Whether a panel has been assigned to this case. ``None``
        if the API did not return a value.
    :ivar originating_cases: Lower court cases from which this case originated.
    :ivar transfers: Transfers of this case between courts.
    :ivar entries: Docket entries filed in this case.
    :ivar parties: Parties in this case.
    :ivar arguments: Oral arguments associated with this case.
    """

    case_uuid: UUID4 = Field(
        validation_alias=AliasPath("caseHeader", "caseInstanceUUID")
    )
    docket_number: Annotated[
        str, AfterValidator(florida_docket_number_validator)
    ] = Field(validation_alias=AliasPath("caseHeader", "caseNumber"))
    case_name: Annotated[str, AfterValidator(harmonize)] = Field(
        validation_alias=AliasPath("caseHeader", "caseTitle")
    )
    case_name_full: Annotated[str, AfterValidator(clean_string)] = Field(
        validation_alias=AliasPath("caseHeader", "caseCaption"), default_factory=lambda d: d["case_name"]
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
    court_id: Annotated[
        str,
        BeforeValidator(
            florida_external_id_to_js_id_validator, json_schema_input_type=str
        ),
    ] = Field(validation_alias=AliasPath("caseHeader", "courtID"))
    court_abbreviation: str = Field(
        validation_alias=AliasPath("caseHeader", "courtAbbreviation"),
        default="",
    )
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
    case_group_flag: bool | None = Field(
        validation_alias=AliasPath("caseHeader", "caseGroupFlag"),
        default=None,
    )
    panel_flag: bool | None = Field(
        validation_alias=AliasPath("caseHeader", "panelFlag"), default=None
    )
    originating_cases: list[FloridaOriginatingCase] = Field(
        validation_alias=AliasPath("caseHeader", "originatingCourtCases"),
        default=[],
    )
    transfers: list[DocketTransfer] = []
    entries: list[FloridaDocketEntry] = []
    parties: list[FloridaParty] = []
    arguments: list[FloridaArgument] = []


class FloridaCaseListParser(FloridaPaginatedResultsParser[FloridaCase]):
    """
    Parser for Florida case list API results.

    :cvar endpoint: The API endpoint for fetching cases from a given court.
    """

    endpoint: ClassVar[str] = "/courts/cms/cases/"

    @override
    def parse_full(self, i: str) -> FloridaPaginatedResults[FloridaCase]:
        return FloridaPaginatedResults[FloridaCase].model_validate_json(i)


class FloridaCaseInfoParser(LegacyParser[FloridaCase]):
    """
    Parser for Florida case info API results.

    :cvar endpoint: The API endpoint for fetching info about a specific case.
    """

    endpoint: ClassVar[str] = "/courts/{court}/cms/cases/{case}"

    @staticmethod
    def populate_transfers(case: FloridaCase) -> None:
        """Populates the ``transfers`` field of a case inplace."""
        case.transfers = [
            DocketTransfer(
                direction=TransferDirection.INBOUND,
                reason=TransferReason.APPEAL,
                court_id=oc.court_id.value,
                docket_number=oc.case_number,
            )
            for oc in case.originating_cases
        ]

    def _parse(self, i: str) -> FloridaCase:
        flc = FloridaCase.model_validate_json(i)
        # I would prefer to use Pydantic's computed_field decorator for this,
        # but type checkers complain if I do so alas.
        self.populate_transfers(flc)
        return flc
