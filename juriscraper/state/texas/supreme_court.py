from juriscraper.lib.string_utils import clean_string
from juriscraper.state.texas.common import (
    CourtID,
    TexasAppealsCourt,
    TexasAppellateBrief,
    TexasCaseEvent,
    TexasCommonData,
    TexasCommonScraper,
    _parse_appeals_court,
)


class TexasSupremeCourtCaseEvent(TexasCaseEvent):
    """
    Extension of `TexasCaseEvent` to allow for the "Remarks" column in Texas
    Supreme Court dockets.

    :ivar remarks: The text content of the relevant cell in the "Remarks"
    column.
    """

    remarks: str


class TexasSupremeCourtAppellateBrief(TexasAppellateBrief):
    """
    Extension of `TexasAppellateBrief` to allow for the "Remarks" column in
    Texas Supreme Court dockets.

    :ivar remarks: The text content of the relevant cell in the "Remarks"
    column.
    """

    remarks: str


class TexasSupremeCourtDocket(TexasCommonData):
    """
    Extension of the `TexasCommonData` schema with data specific to Texas
    Supreme Court dockets.

    :ivar appeals_court: Information about the appeals court which heard this
    case.
    :ivar case_events: A list of `TexasSupremeCourtCaseEvent` objects
    representing the case events.
    :ivar appellate_briefs: A list of `TexasSupremeCourtAppellateBrief` objects
    representing the appellate briefs.
    """

    appeals_court: TexasAppealsCourt
    case_events: list[TexasSupremeCourtCaseEvent]
    appellate_briefs: list[TexasSupremeCourtAppellateBrief]


class TexasSupremeCourtScraper(TexasCommonScraper):
    """
    Extends the `TexasCommonScraper` class to extract data specific to Texas
    Supreme Court dockets. Unique data extracted is:

    - Appeals court information.
    - Remarks on case events and appellate briefs.
    """

    def __init__(self, court_id: str = "texas_sc"):
        super().__init__(court_id)

    @property
    def data(self) -> TexasSupremeCourtDocket:
        """
        Extract parsed data from an HTML tree. This property returns a
        `TexasSupremeCourtDocket`.

        :return: Parsed data.
        """

        common_data = super().data
        case_events = [
            TexasSupremeCourtCaseEvent(
                remarks=clean_string(remarks_element.text_content()),
                **event_data,
            )
            for remarks_element, event_data in zip(
                self.events["Remarks"], common_data["case_events"]
            )
        ]
        appellate_briefs = [
            TexasSupremeCourtAppellateBrief(
                remarks=clean_string(remarks_element.text_content()),
                **event_data,
            )
            for remarks_element, event_data in zip(
                self.briefs["Remarks"], common_data["appellate_briefs"]
            )
        ]

        return TexasSupremeCourtDocket(
            court_id=CourtID.SUPREME_COURT.value,
            appeals_court=_parse_appeals_court(self.tree),
            case_events=case_events,
            appellate_briefs=appellate_briefs,
            docket_number=common_data["docket_number"],
            date_filed=common_data["date_filed"],
            case_type=common_data["case_type"],
            parties=common_data["parties"],
            trial_court=common_data["trial_court"],
            case_name=common_data["case_name"],
            case_name_full=common_data["case_name_full"],
        )
