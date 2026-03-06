import re
from typing import Generic, TypeVar

from pydantic import AliasPath, BaseModel, Field
from pydantic_core import PydanticCustomError

ResultType = TypeVar("ResultType")


class FloridaPaginatedResultsMeta(BaseModel):
    """
    Metadata about Florida paginated API results.

    :ivar page_size: The number of results per page. This should be greater
        than or equal to the length of the results list in
        FloridaPaginatedResults.
    :ivar total_elements: The total number of elements in the results list.
    :ivar total_pages: The total number of pages in the results list.
    :ivar page_number: The page number of the current results list.
    """

    page_size: int = Field(validation_alias="size")
    total_elements: int = Field(validation_alias="totalElements")
    total_pages: int = Field(validation_alias="totalPages")
    page_number: int = Field(validation_alias="number")


class FloridaPaginatedResults(BaseModel, Generic[ResultType]):
    """
    Helper model for parsing Florida paginated API results.

    :ivar results: One page of entries matching the API query.
    :ivar page: Information about the total number of results and the
        pagination state.
    """

    results: list[ResultType] = Field(
        validation_alias=AliasPath("_embedded", "results"), default=[]
    )
    page: FloridaPaginatedResultsMeta


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
