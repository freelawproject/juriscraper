from datetime import datetime
from typing import ClassVar

from pydantic import UUID4, BaseModel, Field

from juriscraper.abstract_parser import AbstractParser
from juriscraper.state.florida.common import FloridaPaginatedResults


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


class FloridaCourtsParser(AbstractParser[list[FloridaCourt]]):
    """
    Parser for Florida court list API results including court IDs needed to
    access other API endpoints.

    Useful for determining if a new court has been added without having to
    check the news.

    :cvar endpoint: The API endpoint for fetching a list of Florida courts.
    """

    endpoint: ClassVar[str] = "/courts"

    def _parse(self, i: str) -> list[FloridaCourt]:
        results = FloridaPaginatedResults[FloridaCourt].model_validate_json(i)
        return results.results
