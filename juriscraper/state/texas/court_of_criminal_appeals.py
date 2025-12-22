from functools import cached_property

from juriscraper.state.texas.common import (
    CourtID,
    TexasAppealsCourt,
    TexasCommonData,
    TexasCommonScraper,
    _parse_appeals_court,
)


class TexasCourtOfCriminalAppealsDocket(TexasCommonData):
    """
    Extension of the `TexasCommonData` schema with data specific to Texas Court
    of Criminal Appeals dockets.

    :ivar appeals_court: Information about the appeals court which heard this
    case.
    """

    appeals_court: TexasAppealsCourt


class TexasCourtOfCriminalAppealsScraper(TexasCommonScraper):
    """
    Extends the `TexasCommonScraper` class to extract data specific to Texas
    Court of Criminal Appeals dockets. Unique data extracted is:

    - Appeals court information.
    """

    def __init__(
        self, court_id: str = CourtID.COURT_OF_CRIMINAL_APPEALS.value
    ):
        super().__init__(court_id)

    @property
    def data(self) -> TexasCourtOfCriminalAppealsDocket:
        """
        Extract parsed data from an HTML tree. This property returns a
        `TexasCourtOfCriminalAppealsDocket`.

        :return: Parsed data.
        """

        common_data = super().data

        return TexasCourtOfCriminalAppealsDocket(
            court_id=CourtID.COURT_OF_CRIMINAL_APPEALS.value,
            appeals_court=_parse_appeals_court(self.tree),
            case_events=common_data["case_events"],
            appellate_briefs=common_data["appellate_briefs"],
            docket_number=common_data["docket_number"],
            date_filed=common_data["date_filed"],
            case_type=common_data["case_type"],
            parties=common_data["parties"],
            trial_court=common_data["trial_court"],
            case_name=common_data["case_name"],
            case_name_full=common_data["case_name_full"],
        )

    @cached_property
    def case_name(self) -> str:
        """
        Special version of case name processing, which handles instances where
        the state is not listed as a party, which we assume to be a clerical
        error. Also eliminates most of the default logic for shortening case
        names as the defendant party's name is typically a person's name, which
        doesn't need to be shortened.

        :return: Shortened case name
        """

        # If there is only one party, and it is not the state, assume there was
        # a clerical error
        if (
            len(self.parties) == 1
            and self.parties[0]["type"].lower().find("state") < 0
        ):
            return f"{self.parties[0]['name']} v. The State of Texas"
        # Fall back on the full case name property
        return self.case_name_full
