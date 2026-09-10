import datetime
from enum import Enum
from uuid import UUID

from core.schemas import HashTag
from features.profile import schemas as profile_schemas
from pydantic import BaseModel, Field


class CallToAction(BaseModel):
    name: str
    value: str


class SupCreatedFromEnum(Enum):
    POST = "POST"
    GIG_LIST = "GIG_LIST"
    ARTIST = "ARTIST"
    EVENT = "EVENT"
    PRO_SERVICE = "PRO_SERVICE"
    CAMPAIGN = "CAMPAIGN"
    MEMBERSHIP = "MEMBERSHIP"
    NONE = "NONE"


# TODO: need to fix event,pro_service,campaign,membership


class SupCreate(BaseModel):
    caption: str = Field(..., min_length=2, max_length=150)
    video_url: str
    thumbnail_url: str
    hashtags: list[HashTag]
    is_membership_only: bool
    is_only_for_followers: bool
    tagged_profiles: list[UUID]
    lat: float | None = None
    long: float | None = None
    location: str
    profile_uuid: UUID
    create_from: SupCreatedFromEnum


class SupOut(SupCreate):
    uuid: UUID
    tagged_profiles_details: list[profile_schemas.ProfileOut]
    created_at: datetime.datetime
    updated_at: datetime.datetime
    is_already_seen: bool


class SupUpdate(BaseModel):
    caption: str | None = None
    video_url: str | None = None
    thumbnail_url: str | None = None
    hashtags: list[HashTag] | None = None
    is_membership_only: bool | None = None
    is_only_for_followers: bool | None = None
    tagged_profiles: list[UUID] | None = None
    uuid: UUID = Field(..., description="Sup's uuid")
    lat: float | None = None
    long: float | None = None
    location: str | None = None
    is_already_seen: bool | None = None


class SupMetadata(BaseModel):
    has_already_liked: bool
    like_count: int
    has_already_shared: bool
    share_count: int
    has_already_viewed: bool
    view_count: int
