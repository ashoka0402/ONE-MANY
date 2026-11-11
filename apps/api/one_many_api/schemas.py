"""Public response contracts and validated account/need request bodies."""

from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator


class RegisterIn(BaseModel):
    email: EmailStr
    display_name: str = Field(min_length=2, max_length=80)
    password: str = Field(min_length=12, max_length=128)

    @field_validator("email")
    @classmethod
    def lowercase_email(cls, email: str) -> str:
        return email.lower()

    @field_validator("display_name")
    @classmethod
    def clean_name(cls, name: str) -> str:
        name = name.strip()
        if len(name) < 2:
            raise ValueError("Display name must contain at least 2 non-whitespace characters")
        return name


class LoginIn(BaseModel):
    email: EmailStr
    password: str

    @field_validator("email")
    @classmethod
    def lowercase_email(cls, email: str) -> str:
        return email.lower()


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    email: EmailStr
    display_name: str
    created_at: datetime


class AuthOut(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int
    user: UserOut


class IntentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    asset_type: str
    purpose: str
    required_features: list[str]
    excluded_features: list[str]
    shareable: bool
    model_name: str
    analyzed_at: datetime


class NeedFields(BaseModel):
    request_text: str = Field(min_length=12, max_length=2000)
    location_label: str | None = Field(default=None, max_length=120)
    needed_from: date | None = None
    needed_until: date | None = None
    discoverable: bool = False

    @field_validator("request_text")
    @classmethod
    def clean_need(cls, text: str) -> str:
        text = text.strip()
        if len(text) < 12:
            raise ValueError("Describe your need in at least 12 characters")
        return text

    @field_validator("location_label")
    @classmethod
    def clean_location(cls, label: str | None) -> str | None:
        return label.strip() or None if label is not None else None

    @model_validator(mode="after")
    def dates_in_order(self) -> "NeedFields":
        if self.needed_from and self.needed_until and self.needed_until < self.needed_from:
            raise ValueError("needed_until cannot precede needed_from")
        return self


class NeedCreate(NeedFields):
    pass


class NeedUpdate(BaseModel):
    request_text: str | None = Field(default=None, min_length=12, max_length=2000)
    location_label: str | None = Field(default=None, max_length=120)
    needed_from: date | None = None
    needed_until: date | None = None
    status: Literal["open", "archived"] | None = None
    discoverable: bool | None = None

    @model_validator(mode="after")
    def validate_changes(self) -> "NeedUpdate":
        if "request_text" in self.model_fields_set:
            if self.request_text is None or len(self.request_text.strip()) < 12:
                raise ValueError("request_text cannot be null or blank")
            self.request_text = self.request_text.strip()
        if "status" in self.model_fields_set and self.status is None:
            raise ValueError("status cannot be null")
        if "discoverable" in self.model_fields_set and self.discoverable is None:
            raise ValueError("discoverable cannot be null")
        if self.location_label is not None:
            self.location_label = self.location_label.strip() or None
        return self


class NeedOut(NeedFields):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    owner_id: UUID
    status: Literal["open", "archived"]
    created_at: datetime
    updated_at: datetime
    intent: IntentOut | None = None


class NeedsPage(BaseModel):
    items: list[NeedOut]
    total: int
    limit: int
    offset: int
