from datetime import datetime
from typing import TypedDict

from lxml import html
from lxml.html import HtmlElement

from juriscraper.lib.html_utils import clean_html, parse_table
from juriscraper.lib.string_utils import clean_string
from juriscraper.scraper import Scraper


class TexasCaseParty(TypedDict):
    """
    Schema for Texas case party details.

    This class is used as a utility to define the necessary attributes for a party and allow type hints.

    :ivar name: The name associated with the party.
    :ivar type: The type of the party (respondent, petitioner, etc.).
    :ivar representatives: A list of representatives associated with the party.
    """

    name: str
    type: str
    representatives: list[str]


class TexasTrialCourt(TypedDict):
    """
    Schema for Texas Trial Court details.

    This class is a `TypedDict` that defines the schema for representing a Texas Trial Court. It is used as a utility for safety and type hints.

    The `judge`, `reporter`, and `punishment` attributes may be empty (most often the `punishment` field will be empty in civil cases), and it is up to the consumer to handle those cases.

    :ivar name: The name of the court.
    :ivar county: The county where the court is located.
    :ivar judge: The name of the presiding judge in the court.
    :ivar case: Specific case identification or name handled by this court.
    :ivar reporter: The name of the court reporter for the case.
    :ivar punishment: The punishment or outcome decided by the court in the case.
    """

    name: str
    county: str
    judge: str
    case: str
    reporter: str
    punishment: str


class TexasCommonData(TypedDict):
    """
    Schema for data common to all Texas dockets.

    This class is a `TypedDict` that defines the schema for representing data common to all Texas dockets. It is used as a utility for safety and type hints.

    :ivar docket_number: The docket number of the case.
    :ivar date_filed: The date the case was filed.
    :ivar case_type: The type of case.
    :ivar parties: A list of parties involved in the case and their associated representatives.
    :ivar trial_court: Information about the trial court handling the case was appealed from.
    """

    docket_number: str
    date_filed: datetime
    case_type: str
    parties: list[TexasCaseParty]
    trial_court: TexasTrialCourt


class TexasCommonScraper(Scraper[TexasCommonData]):
    """
    A scraper for extracting data common to all Texas dockets (Supreme Court, Court of Criminal Appeals, and Court of Appeals).

    Extracts the following data:
    - Docket number
    - Date filed
    - Case type
    - Case parties (name, type, and representatives)
    - Trial court information (court name, county, judge, case number, reporter, and punishment)

    :ivar tree: The HTML tree of the docket page.
    :ivar is_valid: `True` if the HTML tree has been successfully parsed by calling `_parse_text`, `False` otherwise.
    """

    def __init__(self, court_id: str) -> None:
        super().__init__(court_id)
        self.tree: HtmlElement = HtmlElement()
        self.is_valid: bool = False

    def _parse_text(self, text: str) -> None:
        """
        Takes in a string, cleans it, and parses it into an HTML tree. If the
        tree is parsed without raising an exception, the `is_valid` attribute
        is set to `True`.

        :param text: The raw HTML string.
        """
        self.tree = html.fromstring(clean_html(text))
        self.is_valid = True

    @property
    def data(self) -> TexasCommonData:
        """
        Access parsed data from an HTML tree. This property returns the `TexasCommonData`
        `TypedDict` object.

        :raises ValueError: If the `_parse_text` method has not been called yet.

        :return: Parsed data.
        """
        if not self.is_valid:
            raise ValueError("HTML tree has not been parsed yet.")

        data = TexasCommonData(
            docket_number=self._parse_docket_number(),
            date_filed=self._parse_date_filed(),
            case_type=self._parse_case_type(),
            parties=self._parse_parties(),
            trial_court=self._parse_trial_court(),
        )
        return data

    def _parse_docket_number(self) -> str:
        """
        Extracts the docket number from the HTML tree. Will fail if `_parse_text`
        has not yet been called.

        :return: Docket number.
        """
        return clean_string(self.tree.find(
            './/*[@id="case"]/div[2]/div/strong'
        ).text_content())

    def _parse_date_filed(self) -> datetime:
        """
        Extracts the date the case was filed from the HTML tree and parses it into a `datetime` object from mm/dd/yyyy format. Will fail if `_parse_text`
        has not yet been called.

        :return: Date filed
        """
        date_string = clean_string(self.tree.find(
            './/*[@id="case"]/../*[2]/div[2]/div'
        ).text_content())
        return datetime.strptime(date_string, "%m/%d/%Y")

    def _parse_case_type(self) -> str:
        """
        Extracts the case type from the HTML tree. Will fail if `_parse_text`
        has not yet been called.

        :return: Docket number.
        """
        return clean_string(self.tree.find(
            './/*[@id="case"]/../*[3]/div[2]'
        ).text_content())

    def _parse_parties(self) -> list[TexasCaseParty]:
        """
        Extracts the parties from the HTML tree. Multiline entries in the "Representative" column will be treated as if each line is an individual representative for the relevant party. Will fail if `_parse_text`
        has not yet been called.

        :return: Docket number.
        """
        table = self.tree.find('.//table[@id="ctl00_ContentPlaceHolder1_grdParty_ctl00"]')
        parties = parse_table(table)
        n_parties = len(parties["Party"])

        return [
            TexasCaseParty(
                name=parties["Party"][i][0],
                type=parties["PartyType"][i][0],
                representatives=parties["Representative"][i],
            )
            for i in range(n_parties)
        ]

    def _parse_trial_court(self) -> TexasTrialCourt:
        """
        Extracts the trial court info from the HTML tree. Will fail if `_parse_text`
        has not yet been called.

        :return: Trial court info.
        """
        info_panel: HtmlElement = self.tree.find(
            './/*[@id="panelTrialCourtInfo"]/div[2]'
        )
        fields: dict[str, str] = {
            clean_string(child.find(".//*[1]").text_content()): clean_string(
                child.find(".//*[2]").text_content()
            )
            for child in info_panel.iterchildren()
        }

        return TexasTrialCourt(
            name=fields.get("Court", ""),
            county=fields.get("County", ""),
            judge=fields.get("Court Judge", ""),
            case=fields.get("Court Case", ""),
            reporter=fields.get("Reporter", ""),
            punishment=fields.get("Punishment", ""),
        )
