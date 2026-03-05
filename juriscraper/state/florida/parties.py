from typing import ClassVar

from pydantic import UUID4, AliasPath, Field

from juriscraper.state.docket import Party, Representative
from juriscraper.state.florida.api import FloridaPaginatedResults
from juriscraper.state.parser import LegacyParser


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
    party_type: str = Field(
        validation_alias=AliasPath("partyHeader", "partyType")
    )
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

    def validate(self, _output: list[FloridaParty]) -> bool:
        return True

    def _parse(self, i: str) -> list[FloridaParty]:
        party_results = FloridaPaginatedResults[
            FloridaParty
        ].model_validate_json(i)
        return party_results.results
