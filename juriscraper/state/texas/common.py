from datetime import datetime
from typing import TypedDict

from lxml import html
from lxml.html import HtmlElement

from build.lib.juriscraper.lib.html_utils import fix_links_but_keep_anchors
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


class TexasCaseDocument(TypedDict):
    """
    Schema for Texas case document details.

    :ivar url: The URL of the document.
    :ivar name: The name of the document (may be empty).
    """
    url: str
    name: str


class TexasDocketEntry(TypedDict):
    """
    Schema for Texas docket entry details.

    :ivar date: The date of the docket entry.
    :ivar type: The type of the docket entry (e.g., "Notice of appeal received").
    :ivar documents: Any documents associated with the docket entry.
    """
    date: datetime
    type: str
    documents: list[TexasCaseDocument]


class TexasCaseEvent(TexasDocketEntry):
    """
    Extension of `TexasDocketEntry` to handle rows from the "Case Events" table.

    :ivar disposition: The value of the "Disposition" column (e.g., "Filing granted")
    """
    disposition: str


class TexasAppellateBrief(TexasDocketEntry):
    """
    Extension of `TexasDocketEntry` to handle rows from the "Appellate Briefs" table.

    :ivar description: The value of the "Description" column (e.g., "Relator")
    """
    description: str


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
    case_events: list[TexasCaseEvent]
    appellate_briefs: list[TexasAppellateBrief]


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
    date_format = "%m/%d/%Y"
    base_url = "https://search.txcourts.gov"

    def __init__(self, court_id: str) -> None:
        super().__init__(court_id)
        self.tree: HtmlElement = HtmlElement()
        self.events: dict[str, list[HtmlElement]] = {}
        self.briefs: dict[str, list[HtmlElement]] = {}
        self.is_valid: bool = False

    def _parse_text(self, text: str) -> None:
        """
        Takes in a string, cleans it, and parses it into an HTML tree. If the
        tree is parsed without raising an exception, the `is_valid` attribute
        is set to `True`.

        :param text: The raw HTML string.
        """
        self.tree = html.fromstring(clean_html(text))
        self.tree.rewrite_links(fix_links_but_keep_anchors, base_href=self.base_url)
        briefs_table = self.tree.find(
            './/table[@id="ctl00_ContentPlaceHolder1_grdBriefs_ctl00"]'
        )
        events_table = self.tree.find(
            './/table[@id="ctl00_ContentPlaceHolder1_grdEvents_ctl00"]'
        )
        self.events = parse_table(events_table)
        self.briefs = parse_table(briefs_table)
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
            case_events=self._parse_case_events(),
            appellate_briefs=self._parse_appellate_briefs()
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
        return datetime.strptime(date_string, self.date_format)

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
                name=clean_string(parties["Party"][i].text_content()),
                type=clean_string(parties["PartyType"][i].text_content()),
                representatives=[clean_string(text) for text in parties["Representative"][i].xpath(".//text()")],
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

    @staticmethod
    def _parse_case_documents(cell: HtmlElement) -> list[TexasCaseDocument]:
        """
        Helper method to parse case documents for a given docket entry.

        Tries to find a table in the given cell and extracts the document URLs and names from it. If no table is found, returns an empty list.

        :return: List of case documents.
        """
        table = cell.find(".//table")
        if table is None:
            return []
        documents = parse_table(table)
        n = len(documents["0"])

        return [
            TexasCaseDocument(
                url=documents["0"][i].find(".//a").get("href"),
                name=clean_string(documents["1"][i].text_content())
            )
            for i in range(n)
        ]

    def _parse_case_events(self) -> list[TexasCaseEvent]:
        """
        Extracts and parses case events.

        This method processes the "Case Events" table and produces a list of
        TexasCaseEvent objects. If the table is empty, an empty list is returned.

        :return: A list of parsed TexasCaseEvent objects.
        """
        # Works because when there are no entries, Texas places a single <td> element, which will be parsed by parse_table as 1 entry in the first column and 0 in all others.
        if len(self.events["Event Type"]) == 0:
            return []
        n = len(self.events["Date"])

        return [
            TexasCaseEvent(
                date=datetime.strptime(
                    clean_string(self.events["Date"][i].text_content()),
                    self.date_format,
                ),
                type=clean_string(self.events["Event Type"][i].text_content()),
                documents=self._parse_case_documents(self.events["Document"][i]),
                disposition=clean_string(self.events["Disposition"][i].text_content())
            )
            for i in range(n)
        ]

    def _parse_appellate_briefs(self) -> list[TexasAppellateBrief]:
        """
        Extracts and parses appellate briefs.

        This method processes the "Appellate Briefs" table and produces a list of
        TexasAppellateBrief objects. If the table is empty, an empty list is returned.

        :return: A list of parsed TexasAppellateBrief objects.
        """
        # Works because when there are no entries, Texas places a single <td> element, which will be parsed by parse_table as 1 entry in the first column and 0 in all others.
        if len(self.briefs["Event Type"]) == 0:
            return []
        n = len(self.briefs["Date"])

        return [TexasAppellateBrief(
            date=datetime.strptime(clean_string(self.briefs["Date"][i].text_content()), self.date_format),
            type=clean_string(self.briefs["Event Type"][i].text_content()),
            documents=self._parse_case_documents(self.briefs["Document"][i]),
            description=clean_string(self.briefs["Description"][i].text_content())
        ) for i in range(n)]
