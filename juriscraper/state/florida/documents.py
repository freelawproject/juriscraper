from typing import ClassVar

from pydantic import UUID4, AliasPath, Field

from juriscraper.abstract_parser import LegacyParser
from juriscraper.state.docket import Document
from juriscraper.state.florida.common import FloridaPaginatedResults


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
    document_name: str = Field(validation_alias="documentName")
    user_document_state: UUID4 = Field(validation_alias="userDocumentState")
    case_uuid: UUID4 = Field(
        validation_alias=AliasPath("caseHeader", "caseInstanceUUID")
    )
    case_number: str = Field(
        validation_alias=AliasPath("caseHeader", "caseNumber")
    )
    case_title: str = Field(
        validation_alias=AliasPath("caseHeader", "caseTitle")
    )
    court_id: int = Field(validation_alias=AliasPath("caseHeader", "courtID"))
    document_type: str = Field(
        validation_alias=AliasPath("documentInfo", "documentType")
    )
    content_type: str = Field(
        validation_alias=AliasPath("documentInfo", "contentType")
    )
    file_extension: str = Field(
        validation_alias=AliasPath("documentInfo", "fileExtension")
    )
    page_count: int = Field(
        validation_alias=AliasPath("documentInfo", "pageCount")
    )
    file_size: int = Field(
        validation_alias=AliasPath("documentInfo", "fileSize")
    )
    url: str = ""


class FloridaDocumentAccessParser(LegacyParser[list[FloridaDocument]]):
    """
    Parser for Florida document list API results.

    :cvar endpoint: The API endpoint for fetching a document's data.
    """

    endpoint: ClassVar[str] = "/courts/cms/docketentrydocumentaccess"

    def _parse(self, i: str) -> list[FloridaDocument]:
        results = FloridaPaginatedResults[FloridaDocument].model_validate_json(
            i
        )
        return results.results
