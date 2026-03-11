from typing import Annotated, Any, ClassVar

from pydantic import UUID4, AliasPath, BeforeValidator, Field
from pydantic_core import PydanticCustomError

from juriscraper.abstract_parser import AbstractParser
from juriscraper.state.docket import Party, PartyType, Representative
from juriscraper.state.florida.common import FloridaPaginatedResults

FLORIDA_PARTY_TYPE_MAP: dict[str, PartyType] = {
    "appellant": PartyType.APPELLANT,
    "appellant/cross-appellee": PartyType.APPELLANT,
    "petitioner": PartyType.PETITIONER,
    "petitioner/cross-respondent": PartyType.PETITIONER,
    "appellee": PartyType.APPELLEE,
    "appellee/cross-appellant": PartyType.APPELLEE,
    "respondent": PartyType.RESPONDENT,
    "respondent/cross-petitioner": PartyType.RESPONDENT,
    "cross-appellant": PartyType.APPELLANT,
    "cross-appellee": PartyType.APPELLEE,
    "cross-petitioner": PartyType.PETITIONER,
    "cross-respondent": PartyType.RESPONDENT,
    "intervenor": PartyType.UNKNOWN,
    "receiver": PartyType.UNKNOWN,
    "complainant": PartyType.UNKNOWN,
    "amicus - appellant": PartyType.APPELLANT,
    "amicus - no position": PartyType.UNKNOWN,
    "amicus - petitioner": PartyType.PETITIONER,
    "amicus - respondent": PartyType.RESPONDENT,
    "amicus curiae": PartyType.UNKNOWN,
    "bar liaison": PartyType.UNKNOWN,
    "chair-committee": PartyType.UNKNOWN,
    "chair-hearing panel": PartyType.UNKNOWN,
    "commenter": PartyType.UNKNOWN,
    "judge of compensation claims": PartyType.UNKNOWN,
    "judge/judicial officer": PartyType.UNKNOWN,
    "lower tribunal clerk": PartyType.UNKNOWN,
    "opponent": PartyType.UNKNOWN,
    "past chair-committee": PartyType.UNKNOWN,
    "past chair-hearing panel": PartyType.UNKNOWN,
    "past vice chair-committee": PartyType.UNKNOWN,
    "proponent": PartyType.UNKNOWN,
    "sponsor": PartyType.UNKNOWN,
    "vice chair-committee": PartyType.UNKNOWN,
}


def florida_party_type_validator(value: Any) -> PartyType:
    """Validates and converts a Florida party type string to a PartyType
    enum value.

    :param value: The party type string from the API response.

    :return: The corresponding PartyType enum value.

    :raise PydanticCustomError: If the value is not in
        FLORIDA_PARTY_TYPE_MAP.
    """
    s = str(value).lower()
    if s not in FLORIDA_PARTY_TYPE_MAP:
        raise PydanticCustomError(
            "florida_party_type",
            "Unrecognized Florida party type value: {type}.",
            {"type": s},
        )
    return FLORIDA_PARTY_TYPE_MAP[s]


class FloridaPartyRepresentative(Representative):
    """
    Extension of the Representative data structure with Florida-specific
    fields.

    :ivar party_uuid: The UUID of the represented party for use in API
        requests.
    :ivar name: The name of the representative.
    :ivar sort_name: The name used to sort this representative in lists.
    :ivar primary_flag: Whether this is the primary representative of this
        party.
    """

    party_uuid: UUID4 = Field(
        validation_alias=AliasPath("attorneyPartyHeader", "casePartyUUID")
    )
    name: str = Field(
        validation_alias=AliasPath(
            "attorneyPartyHeader", "partyActorInstance", "displayName"
        )
    )
    sort_name: str = Field(
        validation_alias=AliasPath(
            "attorneyPartyHeader", "partyActorInstance", "sortName"
        )
    )
    primary_flag: bool = Field(validation_alias="primaryFlag")


class FloridaParty(Party):
    """
    Extension of the Party data structure with Florida-specific fields.

    :ivar uuid: The UUID of this party for use in API requests.
    :ivar party_type_raw: The party type field as it appears in the API
        response.
    :ivar party_type: Conversion of the party subtype field to the PartyType
        enum.
    :ivar party_type_id: Florida internal integer ID of the party type.
    :ivar party_subtype: The name of the party subtype.
    :ivar party_subtype_id: Florida internal integer ID of the party subtype.
    :ivar status: The status of the party.
    :ivar status_id: Florida internal integer ID of the party status.
    :ivar name: The name of the party.
    :ivar sort_name: Value used to sort this party in lists.
    :ivar pro_se_flag: Whether this party is self-represented.
    :ivar order_by: Unclear what this field represents.
    :ivar representatives: This party's legal representation.
    :ivar non_public_flag: Unclear what this field represents. Should always be
        false.
    :ivar party_number: Unclear what this field represents.
    :ivar involvement_type_id: Florida internal integer ID of this party's type
        of involvement in the case.
    """

    uuid: UUID4 = Field(
        validation_alias=AliasPath("partyHeader", "casePartyUUID")
    )
    party_type_raw: str = Field(
        validation_alias=AliasPath("partyHeader", "partyType")
    )
    party_type: Annotated[
        PartyType,
        BeforeValidator(
            florida_party_type_validator, json_schema_input_type=str
        ),
    ] = Field(validation_alias=AliasPath("partyHeader", "partySubType"))
    party_type_id: int = Field(
        validation_alias=AliasPath("partyHeader", "partyTypeID")
    )
    party_subtype: str = Field(
        validation_alias=AliasPath("partyHeader", "partySubType")
    )
    party_subtype_id: int = Field(
        validation_alias=AliasPath("partyHeader", "partySubTypeID")
    )
    status: str = Field(
        validation_alias=AliasPath("partyHeader", "partyStatus")
    )
    status_id: int = Field(
        validation_alias=AliasPath("partyHeader", "partyStatusID")
    )
    name: str = Field(
        validation_alias=AliasPath(
            "partyHeader", "partyActorInstance", "displayName"
        )
    )
    sort_name: str = Field(
        validation_alias=AliasPath(
            "partyHeader", "partyActorInstance", "sortName"
        )
    )
    pro_se_flag: bool = Field(validation_alias="proSeFlag")
    order_by: int = Field(validation_alias="orderBy")
    representatives: list[FloridaPartyRepresentative] = Field(
        validation_alias="legalRepresentations", default=[]
    )
    non_public_flag: bool = Field(validation_alias="nonPublicFlag")
    party_number: int = Field(validation_alias="partyNumber")
    involvement_type_id: int = Field(validation_alias="involvementTypeID")


class FloridaPartyListParser(AbstractParser[list[FloridaParty]]):
    """
    Parser for Florida party list API results.

    :cvar endpoint: The API endpoint for fetching a case's party list.
    """

    endpoint: ClassVar[str] = "/courts/{court}/cms/cases/{case}/parties"

    def _parse(self, i: str) -> list[FloridaParty]:
        party_results = FloridaPaginatedResults[
            FloridaParty
        ].model_validate_json(i)
        return party_results.results
