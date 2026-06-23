from datetime import datetime
from typing import ClassVar

from pydantic import AliasPath, BaseModel, Field

from juriscraper.state.florida.common import (
    FloridaPaginatedResults,
    FloridaPaginatedResultsParser,
)


class FloridaArgument(BaseModel):
    """
    Data structure to capture the oral arguments associated with Florida dockets.

    These fields are based on API results and don't capture all the fields displayed on the front-end, which we will
    probably find when validation fails.

    :ivar start_date: The date the argument was initiated.
    :ivar hearing_type: The type of hearing, e.g., Oral Argument.
    :ivar hearing_status: The status of the hearing, e.g., Scheduled (I have not found a hearing that was not "Scheduled"
        no matter how far back I go).
    :ivar panel_flag: Presumably whether the argument was heard in front of a panel.
    """

    start_date: datetime = Field(validation_alias="startDate")
    hearing_type: str = Field(validation_alias="hearingType")
    hearing_status: str = Field(validation_alias="hearingStatus")
    panel_flag: bool = Field(validation_alias=AliasPath("event", "panelFlag"))


class FloridaCaseArgumentsParser(
    FloridaPaginatedResultsParser[FloridaArgument]
):
    """
    Parser for Florida case "Oral Arguments" list.

    :cvar endpoint: The API endpoint for fetching hearings.
    """

    endpoint: ClassVar[str] = "courts/{court}/cms/cases/{case}/hearings"

    def parse_full(self, i: str) -> FloridaPaginatedResults[FloridaArgument]:
        return FloridaPaginatedResults[FloridaArgument].model_validate_json(i)
