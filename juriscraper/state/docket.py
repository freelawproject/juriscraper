"""
Defines common schemas for output of state docket parser. Individual parsers
may output additional data, but all should output at least the data defined
here in this format.
"""

from datetime import date
from enum import Enum
from typing import Generic, TypeVar

from pydantic import BaseModel


class Document(BaseModel):
    """
    Represents a docket entry attachment.

    :ivar url: The URL the attachment can be downloaded from.
    """

    url: str


class DocketEntryType(Enum):
    """
    Represents the type of docket entries.
    """

    UNKNOWN = "unknown"
    """A docket entry whose type cannot be determined."""
    BRIEF = "brief"
    """Brief entry type"""
    DISPOSITION = "disposition"
    """Disposition entry type"""
    EVENT = "event"
    """Event entry type"""
    LETTER = "letter"
    """Letter entry type"""
    MOTION = "motion"
    """Motion entry type"""
    NOTICE = "notice"
    """Notice entry type"""
    ORDER = "order"
    """Order entry type"""
    PETITION = "petition"
    """Petition entry type"""


_DocketEntryDocument = TypeVar("_DocketEntryDocument", bound=Document)


class DocketEntry(BaseModel, Generic[_DocketEntryDocument]):
    """
    Represents a single docket entry.

    :ivar date_filed: The date this docket entry was filed with the court.
    :ivar attachments: Documents attached to this entry.
    :ivar entry_type: The type of this entry.
    """

    date_filed: date
    attachments: list[_DocketEntryDocument]
    entry_type: DocketEntryType


class TransferDirection(Enum):
    """
    Represents the direction of a docket transfer.
    """

    INBOUND = "inbound"
    """A transfer into this court."""
    OUTBOUND = "outbound"
    """A transfer out of this court."""


class TransferReason(Enum):
    """
    Represents the reason for transferring a docket.
    """

    APPEAL = "appeal"
    """The case was appealed to a higher court."""
    WORKLOAD = "workload"
    """The case was moved to balance workload between courts at the same level"""
    JURISDICTION = "jurisdiction"
    """The case was moved for jurisdictional reasons."""
    UNKNOWN = "unknown"
    """A transfer reason could not be determined by the parser."""


class DocketTransfer(BaseModel):
    """
    Represents a transfer of a docket from one court to another.

    :ivar direction: Whether the docket is being transferred into or out of the court.
    :ivar reason: The reason for transferring the docket.
    :ivar court_id: The ID of the court this docket is being transferred to or from.
    :ivar docket_number: The docket number in the origin or destination court.
    """

    direction: TransferDirection
    reason: TransferReason
    court_id: str
    docket_number: str


class Representative(BaseModel):
    """
    Someone representing a party in a case (e.g. an attorney).

    :ivar name: The name of the representative.
    """

    name: str


class PartyType(Enum):
    """
    The type of party in a case (e.g. plaintiff, defendant, the state, etc.).
    """

    UNKNOWN = "unknown"
    """The party's type cannot be determined by the parser."""
    APPELLANT = "appellant"
    """Appellant party type"""
    PETITIONER = "petitioner"
    """Petitioner party type"""
    APPELLEE = "appellee"
    """Appellee party type"""
    RESPONDENT = "respondent"
    """Respondent party type"""


_PartyRepresentative = TypeVar("_PartyRepresentative", bound=Representative)


class Party(BaseModel, Generic[_PartyRepresentative]):
    """
    A party in a case.

    :ivar name: The name of the party.
    :ivar party_type: The type of the party.
    :ivar representatives: The representatives of the party.
    """

    name: str
    party_type: PartyType
    representatives: list[_PartyRepresentative]


class DocketType(Enum):
    """
    The type of docket.
    """

    UNKNOWN = "unknown"
    """The docket type cannot be determined by the parser."""
    CIVIL = "civil"
    """Civil cases"""
    CRIMINAL = "criminal"
    """Criminal cases"""
    FAMILY = "family"
    """Family cases"""
    JUVENILE = "juvenile"
    """Juvenile cases"""
    PROBATE = "probate"
    """Probate cases"""
    ADMINISTRATIVE = "administrative"
    """Administrative cases"""
    DEATH_APPEAL = "death_appeal"
    """Death penalty appeal cases"""


_DocketDocketTransfer = TypeVar("_DocketDocketTransfer", bound=DocketTransfer)
_DocketDocketEntry = TypeVar("_DocketDocketEntry", bound=DocketEntry)
_DocketParty = TypeVar("_DocketParty", bound=Party)


class Docket(
    BaseModel, Generic[_DocketDocketTransfer, _DocketDocketEntry, _DocketParty]
):
    """
    Represents one docket in one court.

    :ivar court_id: The ID of the court the docket is in.
    :ivar docket_number: The docket number assigned by the court.
    :ivar case_name: A (potentially) shortened version of the full case name.
    :ivar case_name_full: The full case name with minimal modifications.
    :ivar date_filed: The date this docket was filed with the court.
    :ivar transfers: Transfers of this docket to and from the court.
    :ivar entries: Docket entries that have been filed in this case.
    :ivar parties: Parties in this case.
    :ivar docket_type: The type of this case.
    """

    court_id: str
    docket_number: str
    case_name: str
    case_name_full: str
    date_filed: date
    transfers: list[_DocketDocketTransfer]
    entries: list[_DocketDocketEntry]
    parties: list[_DocketParty]
    docket_type: DocketType


BaseDocket = TypeVar("BaseDocket", bound=Docket)
