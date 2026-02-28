from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class LoopsBaseModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")


class ContactRequest(LoopsBaseModel):
    email: str
    first_name: Optional[str] = Field(default=None, alias="firstName")
    last_name: Optional[str] = Field(default=None, alias="lastName")
    subscribed: Optional[bool] = None
    user_group: Optional[str] = Field(default=None, alias="userGroup")
    user_id: Optional[str] = Field(default=None, alias="userId")
    mailing_lists: Optional[Dict[str, bool]] = Field(default=None, alias="mailingLists")
    source: Optional[str] = None


class UpdateContactRequest(LoopsBaseModel):
    email: Optional[str] = None
    user_id: Optional[str] = Field(default=None, alias="userId")
    first_name: Optional[str] = Field(default=None, alias="firstName")
    last_name: Optional[str] = Field(default=None, alias="lastName")
    subscribed: Optional[bool] = None
    user_group: Optional[str] = Field(default=None, alias="userGroup")
    mailing_lists: Optional[Dict[str, bool]] = Field(default=None, alias="mailingLists")
    source: Optional[str] = None

    @model_validator(mode="after")
    def validate_identifier(self) -> "UpdateContactRequest":
        if not self.email and not self.user_id:
            raise ValueError("Either email or user_id must be provided")
        return self


class FindContactQuery(LoopsBaseModel):
    email: Optional[str] = None
    user_id: Optional[str] = Field(default=None, alias="userId")

    @model_validator(mode="after")
    def validate_identifier(self) -> "FindContactQuery":
        if bool(self.email) == bool(self.user_id):
            raise ValueError("Provide exactly one of email or user_id")
        return self


class DeleteContactRequest(LoopsBaseModel):
    email: Optional[str] = None
    user_id: Optional[str] = Field(default=None, alias="userId")

    @model_validator(mode="after")
    def validate_identifier(self) -> "DeleteContactRequest":
        if not self.email and not self.user_id:
            raise ValueError("Either email or user_id must be provided")
        return self


PropertyType = Literal["string", "number", "boolean", "date"]


class CreateContactPropertyRequest(LoopsBaseModel):
    name: str
    label: str | None = None
    type: PropertyType


class SendEventRequest(LoopsBaseModel):
    email: Optional[str] = None
    user_id: Optional[str] = Field(default=None, alias="userId")
    event_name: str = Field(alias="eventName")
    event_properties: Optional[Dict[str, Any]] = Field(default=None, alias="eventProperties")
    mailing_lists: Optional[Dict[str, bool]] = Field(default=None, alias="mailingLists")

    @model_validator(mode="after")
    def validate_identifier(self) -> "SendEventRequest":
        if not self.email and not self.user_id:
            raise ValueError("Either email or user_id must be provided")
        return self


class Attachment(LoopsBaseModel):
    filename: str
    content_type: str = Field(alias="contentType")
    data: str


class SendTransactionalEmailRequest(LoopsBaseModel):
    transactional_id: str = Field(alias="transactionalId")
    email: str
    data_variables: Optional[Dict[str, Any]] = Field(default=None, alias="dataVariables")
    add_to_audience: Optional[bool] = Field(default=None, alias="addToAudience")
    attachments: Optional[List[Attachment]] = None


class ContactUpsertResponse(LoopsBaseModel):
    success: bool
    id: str


class SuccessResponse(LoopsBaseModel):
    success: bool


class ApiKeyResponse(LoopsBaseModel):
    success: bool
    team_name: str = Field(alias="teamName")


class Contact(LoopsBaseModel):
    id: str
    email: str


class ContactProperty(LoopsBaseModel):
    key: str
    label: str
    type: str


class MailingList(LoopsBaseModel):
    id: str
    name: str
    description: str
    is_public: bool = Field(alias="isPublic")


class TransactionalEmail(LoopsBaseModel):
    id: str
    name: str
    last_updated: str = Field(alias="lastUpdated")
    data_variables: List[str] = Field(alias="dataVariables")


class Pagination(LoopsBaseModel):
    next_cursor: Optional[str] = Field(default=None, alias="nextCursor")


class TransactionalEmailListResponse(LoopsBaseModel):
    pagination: Pagination
    data: List[TransactionalEmail]
