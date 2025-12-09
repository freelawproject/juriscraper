
from build.lib.juriscraper.lib.string_utils import clean_string
from juriscraper.state.texas.common import (
    TexasAppealsCourt,
    TexasAppellateBrief,
    TexasCaseEvent,
    TexasCommonData,
    TexasCommonScraper,
)


class TexasSupremeCourtCaseEvent(TexasCaseEvent):
    """
    Extension of `TexasCaseEvent` to allow for the "Remarks" column in Texas Supreme Court dockets.

    :ivar remarks: The text content of the relevant cell in the "Remarks" column.
    """
    remarks: str

class TexasSupremeCourtAppellateBrief(TexasAppellateBrief):
    """
    Extension of `TexasAppellateBrief` to allow for the "Remarks" column in Texas Supreme Court dockets.

    :ivar remarks: The text content of the relevant cell in the "Remarks" column.
    """
    remarks: str

class TexasSupremeCourtDocket(TexasCommonData):
    """
    Extension of the `TexasCommonData` schema with data specific to Texas Supreme Court dockets.
    :ivar appeals_court: Information about the appeals court which heard this case.
    :ivar case_events: A list of `TexasSupremeCourtCaseEvent` objects representing the case events.
    :ivar appellate_briefs: A list of `TexasSupremeCourtAppellateBrief` objects representing the appellate briefs.
    """
    appeals_court: TexasAppealsCourt
    case_events: list[TexasSupremeCourtCaseEvent]
    appellate_briefs: list[TexasSupremeCourtAppellateBrief]

class TexasSupremeCourtScraper(TexasCommonScraper):
    """
    Extends the `TexasCommonScraper` class to extract data specific to Texas Supreme Court dockets. Unique data extracted is:

    - Appeals court information.
    - Remarks on case events and appellate briefs.
    """
    def __init__(self, court_id: str = "texas_sc"):
        super().__init__(court_id)

    @property
    def data(self) -> TexasSupremeCourtDocket:
        """
        Extract parsed data from an HTML tree. This property returns a `TexasSupremeCourtDocket`.

        :return: Parsed data.
        """
        common_data = super().data
        case_events = [
            TexasSupremeCourtCaseEvent(
                remarks=clean_string(self.events["Remarks"][i].text_content()),
                **common_data["case_events"][i]
            )
            for i in range(len(common_data["case_events"]))
        ]
        appellate_briefs = [
            TexasSupremeCourtAppellateBrief(
                remarks=clean_string(self.events["Remarks"][i].text_content()),
                **common_data["appellate_briefs"][i]
            )
            for i in range(len(common_data["appellate_briefs"]))
        ]

        return TexasSupremeCourtDocket(
            appeals_court=self._parse_appeals_court(),
            case_events=case_events,
            appellate_briefs=appellate_briefs,
            docket_number=common_data["docket_number"],
            date_filed=common_data["date_filed"],
            case_type=common_data["case_type"],
            parties=common_data["parties"],
            trial_court=common_data["trial_court"],
        )

    def _parse_appeals_court(self) -> TexasAppealsCourt:
        """
        Parses the appeals court information and constructs a `TexasAppealsCourt` instance.

        :return: Extracted appeals court information.
        """
        container = self.tree.find('.//*[@id="ctl00_ContentPlaceHolder1_divCOAInfo"]/div/div/div[2]')
        info_container = container.find('.//*[@id="ctl00_ContentPlaceHolder1_pnlCOA"]')
        # Texas gives the judge their own child element all to themselves for some reason.
        judge_container = container.find('.//*[@id="ctl00_ContentPlaceHolder1_pnlCOAJudge"]')
        case_info = {
            clean_string(row.find('.//*[1]').text_content()): row.find('.//*[2]')
            for row in (list(info_container) + list(judge_container))
        }

        return TexasAppealsCourt(
            case_number=clean_string(case_info["COA Case"].text_content()),
            case_url=case_info["COA Case"].find(".//a").get("href"),
            disposition=clean_string(case_info["Disposition"].text_content()),
            opinion_cite=clean_string(case_info["Opinion Cite"].text_content()),
            district=clean_string(case_info["COA District"].text_content()),
            justice=clean_string(case_info["COA Justice"].text_content()),
        )
