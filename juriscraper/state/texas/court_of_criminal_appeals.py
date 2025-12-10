from juriscraper.state.texas.common import (
    CourtID,
    TexasAppealsCourt,
    TexasCommonData,
    TexasCommonScraper,
    _parse_appeals_court,
)


class TexasCourtOfCriminalAppealsDocket(TexasCommonData):
    appeals_court: TexasAppealsCourt


class TexasCourtOfCriminalAppealsScraper(TexasCommonScraper):
    """
    Extends the `TexasCommonScraper` class to extract data specific to Texas Court of Criminal Appeals dockets. Unique data extracted is:

    - Appeals court information.
    """

    def __init__(self, court_id: str = "texas_coc"):
        super().__init__(court_id)

    @property
    def data(self) -> TexasCourtOfCriminalAppealsDocket:
        """
        Extract parsed data from an HTML tree. This property returns a `TexasCourtOfCriminalAppealsDocket`.

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
        )
