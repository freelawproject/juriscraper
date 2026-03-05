import re
from typing import Generic, TypeVar

from pydantic import AliasPath, BaseModel, Field
from pydantic_core import PydanticCustomError

ResultType = TypeVar("ResultType")


class FloridaPaginatedResultsMeta(BaseModel):
    page_size: int = Field(alias="size")
    total_elements: int = Field(alias="totalElements")
    total_pages: int = Field(alias="totalPages")
    page_number: int = Field(alias="number")


class FloridaPaginatedResults(BaseModel, Generic[ResultType]):
    results: list[ResultType] = Field(
        validation_alias=AliasPath("_embedded", "results"), default=[]
    )
    page: FloridaPaginatedResultsMeta


class FloridaCasePartyType(BaseModel):
    id: int = Field(alias="participantTypeID")
    name: str = Field(alias="participantTypeName")
    comment: str = Field(alias="participantTypeComment")


class FloridaCaseInvolvementType(BaseModel):
    id: int = Field(alias="involvementTypeID")
    name: str = Field(alias="involvementTypeName")
    comment: str = Field(alias="involvementTypeComment")


class FloridaCasePartySubType(BaseModel):
    id: int = Field(alias="participantSubTypeID")
    name: str = Field(alias="participantSubTypeName")
    comment: str = Field(alias="participantSubTypeComment")
    party_type: FloridaCasePartyType = Field(alias="participantType")
    involvement_type: FloridaCaseInvolvementType = Field(
        alias="involvementType"
    )


class FloridaDocketEntryType(BaseModel):
    id: int = Field(alias="docketEntryTypeID")
    name: str = Field(alias="docketEntryTypeName")
    comment: str = Field(alias="docketEntryTypeComment")


class FloridaDocketEntrySubType(BaseModel):
    id: int = Field(alias="docketEntrySubTypeID")
    name: str = Field(alias="docketEntrySubTypeName")
    comment: str = Field(alias="docketEntrySubTypeComment")
    docket_entry_type: FloridaDocketEntryType = Field(alias="docketEntryType")


class FloridaCaseCategory(BaseModel):
    id: int = Field(alias="caseCategoryID")
    name: int = Field(alias="caseCategoryName")
    comment: str = Field(alias="caseCategoryComment")


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
