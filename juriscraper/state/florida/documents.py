from typing import ClassVar

from pydantic import UUID4, AliasPath, Field

from juriscraper.state.docket import Document
from juriscraper.state.florida.api import FloridaPaginatedResults
from juriscraper.state.parser import LegacyParser


class FloridaDocument(Document):
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
    endpoint: ClassVar[str] = "/courts/cms/docketentrydocumentaccess"

    def _parse(self, i: str) -> list[FloridaDocument]:
        results = FloridaPaginatedResults[FloridaDocument].model_validate_json(
            i
        )
        return results.results
