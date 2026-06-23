from datetime import datetime
from enum import Enum
from typing import ClassVar

from pydantic import UUID4, BaseModel, Field

from juriscraper.abstract_parser import LegacyParser
from juriscraper.state.florida.common import FloridaPaginatedResults


class FloridaCourtID(Enum):
    """
    Standardized IDs for Florida courts.
    """

    SUPREME_COURT = "flsc"
    """Florida Supreme Court"""
    FIRST_COA = "flca01"
    """Florida First Court of Appeals"""
    SECOND_COA = "flca02"
    """Florida Second Court of Appeals"""
    THIRD_COA = "flca03"
    """Florida Third Court of Appeals"""
    FOURTH_COA = "flca04"
    """Florida Fourth Court of Appeals"""
    FIFTH_COA = "flca05"
    """Florida Fifth Court of Appeals"""
    SIXTH_COA = "flca06"
    """Florida Sixth Court of Appeals"""
    CIRCUIT = "flcrct"
    """Florida circuit courts"""
    COUNTY = "flcnty"
    """Florida county courts"""
    ADMINISTRATIVE_AGENCY = "fladma"
    """Florida administrative agencies (used as a value in the originating court info)."""
    DOAH = "fldoah"
    """Florida Division of Administrative Hearings"""
    COMPENSATION_CLAIMS = "flcomp"
    """Florida Office of the Judges of Compensation Claims"""
    US_COA = "uscoa"
    """United States Court of Appeals"""
    UNKNOWN = "flunknown"
    """Unknown Florida court"""
    UNASSIGNED = "unassigned"
    """Unassigned court. Indicates parser needs to be updated."""


FLORIDA_COURT_EXTERNAL_ID_MAP: dict[str, FloridaCourtID] = {
    "1": FloridaCourtID.SUPREME_COURT,
    "2": FloridaCourtID.FIRST_COA,
    "3": FloridaCourtID.SECOND_COA,
    "4": FloridaCourtID.THIRD_COA,
    "5": FloridaCourtID.FOURTH_COA,
    "6": FloridaCourtID.FIFTH_COA,
    "7": FloridaCourtID.SIXTH_COA,
}


class FloridaCourtLocation(BaseModel):
    """
    A location within a Florida court.

    :ivar calendar_event_flag: Purpose unclear. Whether this location has
        calendar events?
    :ivar case_location_flag: Purpose unclear.
    :ivar location_comment: A comment or note about this location.
    :ivar location_id: Florida internal integer ID of this location.
    :ivar location_name: The name of this location.
    """

    calendar_event_flag: bool = Field(validation_alias="calendarEventFlag")
    case_location_flag: bool = Field(validation_alias="caseLocationFlag")
    location_comment: str = Field(validation_alias="locationComment")
    location_id: int = Field(validation_alias="locationID")
    location_name: str = Field(validation_alias="locationName")


class FloridaCourt(BaseModel):
    """
    A Florida court as returned by the courts API.

    :ivar active: Whether this court is currently active.
    :ivar display_name: The display name of the court.
    :ivar external_identifier: An external numeric identifier for the court.
    :ivar modified_date: The date this court record was last modified.
    :ivar modified_user_id: The UUID of the user who last modified this record.
    :ivar note: A note or comment about this court.
    :ivar resource_id: The UUID resource identifier for this court.
    :ivar locations: Locations within this court.
    """

    active: bool = Field(validation_alias="active")
    display_name: str = Field(validation_alias="displayName")
    external_identifier: int = Field(validation_alias="externalIdentifier")
    modified_date: datetime = Field(validation_alias="modifiedDate")
    modified_user_id: UUID4 = Field(validation_alias="modifiedUserID")
    note: str = Field(validation_alias="note")
    resource_id: UUID4 = Field(validation_alias="resourceID")
    locations: list[FloridaCourtLocation] = Field(validation_alias="locations")


class FloridaCourtsParser(LegacyParser[list[FloridaCourt]]):
    """
    Parser for Florida court list API results including court IDs needed to
    access other API endpoints.

    Useful for determining if a new court has been added without having to
    check the news.

    :cvar endpoint: The API endpoint for fetching a list of Florida courts.
    """

    endpoint: ClassVar[str] = "/courts"
    params: ClassVar[dict[str, str]] = {"fields": "*,locations(*)"}

    def _parse(self, i: str) -> list[FloridaCourt]:
        results = FloridaPaginatedResults[FloridaCourt].model_validate_json(i)
        return results.results
