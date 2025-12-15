from juriscraper.lib.string_utils import clean_string
from juriscraper.state.texas.common import (
    COA_ID_MAP,
    TexasCommonData,
    TexasCommonScraper,
)


class TexasCourtOfAppealsDocket(TexasCommonData):
    publication_service: str


class TexasCourtOfAppealsScraper(TexasCommonScraper):
    def __init__(self, court_id: str):
        super().__init__(court_id)

    @property
    def data(self) -> TexasCourtOfAppealsDocket:
        common_data = super().data
        court_name = self._parse_court_name()

        return TexasCourtOfAppealsDocket(
            court_id=COA_ID_MAP[court_name.lower()].value,
            case_events=common_data["case_events"],
            appellate_briefs=common_data["appellate_briefs"],
            docket_number=common_data["docket_number"],
            date_filed=common_data["date_filed"],
            case_type=common_data["case_type"],
            parties=common_data["parties"],
            trial_court=common_data["trial_court"],
            case_name=common_data["case_name"],
            case_name_full=common_data["case_name_full"],
            publication_service=self.case_data["pub service"],
        )

    def _parse_court_name(self) -> str:
        return clean_string(self.tree.find(".//h1").text_content())
