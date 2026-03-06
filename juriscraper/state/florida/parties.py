from typing import Annotated, Any, ClassVar

from pydantic import UUID4, AliasPath, BeforeValidator, Field
from pydantic_core import PydanticCustomError

from juriscraper.state.docket import Party, PartyType, Representative
from juriscraper.state.florida.common import FloridaPaginatedResults
from juriscraper.state.parser import LegacyParser

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
    s = str(value).lower()
    if s not in FLORIDA_PARTY_TYPE_MAP:
        raise PydanticCustomError(
            "florida_docket_entry_type",
            "Unrecognized Florida party type value: {type}.",
            {"type": s},
        )
    return FLORIDA_PARTY_TYPE_MAP[s]


class FloridaPartyRepresentative(Representative):
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


class FloridaPartyListParser(LegacyParser[list[FloridaParty]]):
    endpoint: ClassVar[str] = "/courts/{court}/cms/cases/{case}/parties"

    def _parse(self, i: str) -> list[FloridaParty]:
        party_results = FloridaPaginatedResults[
            FloridaParty
        ].model_validate_json(i)
        return party_results.results
