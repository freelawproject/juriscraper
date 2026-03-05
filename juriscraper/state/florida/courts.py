from datetime import datetime
from typing import ClassVar

from pydantic import UUID4, BaseModel, Field

from juriscraper.state.florida.common import FloridaPaginatedResults
from juriscraper.state.parser import LegacyParser


class FloridaCourtLocation(BaseModel):
    calendar_event_flag: bool = Field(validation_alias="calendarEventFlag")
    case_location_flag: bool = Field(validation_alias="caseLocationFlag")
    location_comment: str = Field(validation_alias="locationComment")
    location_id: int = Field(validation_alias="locationID")
    location_name: str = Field(validation_alias="locationName")


class FloridaCourt(BaseModel):
    active: bool = Field(validation_alias="active")
    display_name: str = Field(validation_alias="displayName")
    external_identifier: int = Field(validation_alias="externalIdentifier")
    modified_date: datetime = Field(validation_alias="modifiedDate")
    modified_user_id: UUID4 = Field(validation_alias="modifiedUserID")
    note: str = Field(validation_alias="note")
    resource_id: UUID4 = Field(validation_alias="resourceID")
    locations: list[FloridaCourtLocation] = Field(validation_alias="locations")


class FloridaCourtsParser(LegacyParser[list[FloridaCourt]]):
    endpoint: ClassVar[str] = "/courts"

    def _parse(self, i: str) -> list[FloridaCourt]:
        results = FloridaPaginatedResults[FloridaCourt].model_validate_json(i)
        return results.results
