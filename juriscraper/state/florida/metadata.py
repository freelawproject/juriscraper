from pydantic import BaseModel, Field


class ParticipantType(BaseModel):
    id: int = Field(validation_alias="participantTypeID")
    name: str = Field(validation_alias="participantTypeName")
    comment: str = Field(validation_alias="participantTypeComment")


class InvolvementType(BaseModel):
    id: int = Field(validation_alias="involvementTypeID")
    value: str = Field(validation_alias="involvementTypeValue")
    comment: str = Field(validation_alias="involvementTypeComment")


class CasePartySubType(BaseModel):
    id: int = Field(validation_alias="participantSubTypeID")
    name: str = Field(validation_alias="participantSubTypeName")
    comment: str = Field(validation_alias="participantSubTypeComment")
    participant_type: ParticipantType = Field(
        validation_alias="participantType"
    )
    involvement_type: InvolvementType = Field(
        validation_alias="involvementType"
    )


class CaseCategory(BaseModel):
    id: int = Field(validation_alias="caseCategoryID")
    name: str = Field(validation_alias="caseCategoryName")
    comment: str = Field(validation_alias="caseCategoryComment")


class DocketEntryType(BaseModel):
    id: int = Field(validation_alias="docketEntryTypeID")
    name: str = Field(validation_alias="docketEntryTypeName")
    comment: str = Field(validation_alias="docketEntryTypeComment")


class DocketEntrySubType(BaseModel):
    id: int = Field(validation_alias="docketEntrySubTypeID")
    name: str = Field(validation_alias="docketEntrySubTypeName")
    comment: str = Field(validation_alias="docketEntrySubTypeComment")
    docket_entry_type: DocketEntryType = Field(
        validation_alias="docketEntryType"
    )
