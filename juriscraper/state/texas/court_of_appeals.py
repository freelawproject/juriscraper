from datetime import datetime
from typing import Optional, TypedDict

from juriscraper.lib.string_utils import clean_string
from juriscraper.state.texas.common import (
    TexasCommonData,
    TexasCommonScraper,
    coa_name_to_court_id,
)


class TexasAppealsCourtTransfer(TypedDict):
    """
    Texas Appeals Courts transfer cases in and out to balance workload across
    the state. This class captures details about one of these transfers.

    :ivar court_id: The ID of the court the case was transferred to or from.
    :ivar date: The date the case was transferred.
    :ivar origin_docket: The docket number of the case in the court initiating
    the transfer.
    """

    court_id: str
    date: datetime
    origin_docket: str


class TexasCourtOfAppealsDocket(TexasCommonData):
    """
    Extension of the `TexasCommonData` schema with data specific to Texas Court
    of Appeals dockets.

    :ivar publication_service: The name of the publication service that
    published the case. Value may be an empty string.
    :ivar transfer_from: Details about the transfer from another court of
    appeals, if available.
    :ivar transfer_to: Details about the transfer to another court of appeals,
    if available.
    """

    publication_service: str
    transfer_from: Optional[TexasAppealsCourtTransfer]
    transfer_to: Optional[TexasAppealsCourtTransfer]


class TexasCourtOfAppealsScraper(TexasCommonScraper):
    """
    Extends the `TexasCommonScraper` class to extract data specific to Texas
    Court of Appeals dockets. Unique data extracted is:

    - Publication service name (if available).
    - Transfer information (if available).
    """

    def __init__(self, court_id: str):
        super().__init__(court_id)

    @property
    def data(self) -> TexasCourtOfAppealsDocket:
        """
        Extract parsed data from a docket page.

        :return: Parsed data.
        """

        common_data = super().data
        court_name = clean_string(self.tree.find(".//h1").text_content())
        transfer_from, transfer_to = self._parse_transfers()

        return TexasCourtOfAppealsDocket(
            court_id=coa_name_to_court_id(court_name).value,
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
            transfer_to=transfer_to,
            transfer_from=transfer_from,
        )

    def _parse_transfers(
        self,
    ) -> tuple[
        Optional[TexasAppealsCourtTransfer],
        Optional[TexasAppealsCourtTransfer],
    ]:
        """
        Parses transfer information from the provided case data and returns
        details about transfers both from and to other courts of appeal, if
        available.

        :return: A tuple with the first element containing details about the
        transfer from court, and the second element containing details about
        the transfer to court. Either or both of these values may be None if no
        transfer information is available.
        """

        transfer_from_court = self.case_data["transfer from"]
        transfer_from_date = self.case_data["transfer in"]
        docket_number = self.case_data["transfer case"]
        transfer_to_court = self.case_data["transfer to"]
        transfer_to_date = self.case_data["transfer out"]

        transfer_from = None
        transfer_to = None

        if len(transfer_from_court) > 0:
            transfer_from = TexasAppealsCourtTransfer(
                court_id=coa_name_to_court_id(transfer_from_court).value,
                date=datetime.strptime(transfer_from_date, "%m/%d/%Y"),
                origin_docket=docket_number,
            )
        if len(transfer_to_court) > 0:
            transfer_to = TexasAppealsCourtTransfer(
                court_id=coa_name_to_court_id(transfer_to_court).value,
                date=datetime.strptime(transfer_to_date, "%m/%d/%Y"),
                origin_docket=self.docket_number,
            )

        return transfer_from, transfer_to
