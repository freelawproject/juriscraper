import re
from typing import Generic, TypeVar

from pydantic import AliasPath, BaseModel, Field
from pydantic_core import PydanticCustomError

ResultType = TypeVar("ResultType")


class FloridaPaginatedResultsMeta(BaseModel):
    page_size: int = Field(validation_alias="size")
    total_elements: int = Field(validation_alias="totalElements")
    total_pages: int = Field(validation_alias="totalPages")
    page_number: int = Field(validation_alias="number")


class FloridaPaginatedResults(BaseModel, Generic[ResultType]):
    results: list[ResultType] = Field(
        validation_alias=AliasPath("_embedded", "results"), default=[]
    )
    page: FloridaPaginatedResultsMeta


class FloridaCasePartyType(BaseModel):
    id: int = Field(validation_alias="participantTypeID")
    name: str = Field(validation_alias="participantTypeName")
    comment: str = Field(validation_alias="participantTypeComment")


class FloridaCaseInvolvementType(BaseModel):
    id: int = Field(validation_alias="involvementTypeID")
    name: str = Field(validation_alias="involvementTypeName")
    comment: str = Field(validation_alias="involvementTypeComment")


class FloridaCasePartySubType(BaseModel):
    id: int = Field(validation_alias="participantSubTypeID")
    name: str = Field(validation_alias="participantSubTypeName")
    comment: str = Field(validation_alias="participantSubTypeComment")
    party_type: FloridaCasePartyType = Field(
        validation_alias="participantType"
    )
    involvement_type: FloridaCaseInvolvementType = Field(
        validation_alias="involvementType"
    )


class FloridaDocketEntryType(BaseModel):
    id: int = Field(validation_alias="docketEntryTypeID")
    name: str = Field(validation_alias="docketEntryTypeName")
    comment: str = Field(validation_alias="docketEntryTypeComment")


class FloridaDocketEntrySubType(BaseModel):
    id: int = Field(validation_alias="docketEntrySubTypeID")
    name: str = Field(validation_alias="docketEntrySubTypeName")
    comment: str = Field(validation_alias="docketEntrySubTypeComment")
    docket_entry_type: FloridaDocketEntryType = Field(
        validation_alias="docketEntryType"
    )


FLORIDA_DN_RE = re.compile(r"(?:[1-6]D|SC)\d{4}-\d{4,5}")


def florida_docket_number_validator(dn: str) -> str:
    """
    Validates that Florida docket numbers are a recognized format, raising
    an exception if they are not.

    :param dn: Florida docket number

    :return: Florida docket number unchanged

    :raise: PydanticCustomError
    """

    if not FLORIDA_DN_RE.fullmatch(dn):
        raise PydanticCustomError(
            "florida_docket_number_validator",
            "Unrecognized Florida docket number format: {dn}.",
            {"dn": dn},
        )

    return dn
