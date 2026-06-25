from typing import Annotated, ClassVar

from pydantic import UUID4, AfterValidator, AliasPath, Field
from typing_extensions import override

from juriscraper.state.docket import Document
from juriscraper.state.florida.common import (
    FloridaPaginatedResults,
    FloridaPaginatedResultsParser,
    florida_docket_number_validator,
)


class FloridaDocument(Document):
    """
    Extension of the Document data structure with Florida-specific fields.

    :ivar docket_entry_uuid: The UUID of the parent docket entry.
    :ivar document_link_uuid: The UUID used to construct the document download
        link.
    :ivar document_name: The name of the document.
    :ivar user_document_state: Purpose unclear.
    :ivar case_uuid: The UUID of the case this document belongs to.
    :ivar case_number: The case number this document belongs to.
    :ivar case_title: The title of the case this document belongs to.
    :ivar court_id: Florida internal integer ID of the court.
    :ivar document_type: The type of the document.
    :ivar content_type: The MIME content type of the document.
    :ivar file_extension: The file extension of the document.
    :ivar page_count: The number of pages in the document.
    :ivar file_size: The file size in bytes.
    :ivar url: The URL the document can be downloaded from.
    """

    docket_entry_uuid: UUID4 = Field(validation_alias="docketEntryUUID")
    document_link_uuid: UUID4 = Field(validation_alias="documentLinkUUID")
    document_name: str = Field(
        validation_alias="documentName",
        default="",
    )
    user_document_state: UUID4 = Field(validation_alias="userDocumentState")
    case_uuid: UUID4 = Field(
        validation_alias=AliasPath("caseHeader", "caseInstanceUUID")
    )
    case_number: Annotated[
        str, AfterValidator(florida_docket_number_validator)
    ] = Field(validation_alias=AliasPath("caseHeader", "caseNumber"))
    case_title: str = Field(
        validation_alias=AliasPath("caseHeader", "caseTitle"),
        default="",
    )
    court_id: int = Field(validation_alias=AliasPath("caseHeader", "courtID"))
    document_type: str | None = Field(
        validation_alias=AliasPath("documentInfo", "documentType"),
        default=None,
    )
    content_type: str | None = Field(
        validation_alias=AliasPath("documentInfo", "contentType"),
        default=None,
    )
    file_extension: str | None = Field(
        validation_alias=AliasPath("documentInfo", "fileExtension"),
        default=None,
    )
    page_count: int | None = Field(
        validation_alias=AliasPath("documentInfo", "pageCount"),
        default=None,
    )
    file_size: int | None = Field(
        validation_alias=AliasPath("documentInfo", "fileSize"),
        default=None,
    )
    url: str = ""


class FloridaDocumentAccessParser(
    FloridaPaginatedResultsParser[FloridaDocument]
):
    """
    Parser for Florida document list API results.

    :cvar endpoint: The API endpoint for fetching a document's data.
    """

    endpoint: ClassVar[str] = "/courts/cms/docketentrydocumentsaccess"

    @override
    def parse_full(self, i: str) -> FloridaPaginatedResults[FloridaDocument]:
        return FloridaPaginatedResults[FloridaDocument].model_validate_json(i)
