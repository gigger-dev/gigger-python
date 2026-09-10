import datetime
from typing import Dict, List
from uuid import UUID

from core import schemas as core_schemas
from features.gig_list.schemas import GigListOut
from features.profile import schemas
from pydantic import BaseModel, ConfigDict, Field, field_validator


class PostPositionMetadata(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "profile_uuid": "c9572e3d-a005-471b-bbc8-35103c364057",
                "layout": {
                    "1": "c9572e3d-a005-471b-bbc8-35103c364057",
                    "2": "31db2eef-b358-4ae8-bf26-a968fa74447f",
                },
            }
        },
    )
    profile_uuid: UUID
    layout: Dict[int, str] = Field(
        ..., description="Mapping of positions (1-9) to post UUIDs"
    )

    @field_validator("layout")
    @classmethod
    def validate_positions(cls, v):
        if len(v) > 9:
            raise ValueError("The dictionary must have exactly 9 positions.")
        for key in v.keys():
            if not (1 <= key <= 9):
                raise ValueError(f"Position {key} must be between 1 and 9.")
        for value in v.values():
            if not isinstance(UUID(value), UUID):
                raise ValueError("All values in the dictionary must be UUIDs.")
        return v


class PostCreate(BaseModel):
    post_title: str
    caption: str
    music_title: str
    profile_uuid: UUID
    is_private: bool
    is_membership_only: bool
    is_only_for_followers: bool

    video_url: str
    thumbnail_url: str
    hashtags: list[core_schemas.HashTag]

    tagged_profiles: list[UUID]

    lat: float | None = None
    long: float | None = None
    location: str
    is_draft: bool = False


class PostUpdate(BaseModel):
    profile_uuid: UUID
    uuid: UUID = Field(..., description="Post's uuid")
    post_title: str | None = None
    caption: str | None = None
    music_title: str | None = None

    is_private: bool | None = None
    is_membership_only: bool | None = None
    is_only_for_followers: bool | None = None

    video_url: str | None = None
    thumbnail_url: str | None = None

    hashtags: list[core_schemas.HashTag] | None = None

    tagged_profiles: list[UUID] | None = None

    lat: float | None = None
    long: float | None = None
    location: str | None = None
    is_draft: bool | None = None


class PostOut(PostCreate):
    uuid: UUID
    tagged_profiles_details: list[schemas.ProfileFewerDetailsOut]
    created_at: datetime.datetime
    updated_at: datetime.datetime
    view_count: int


class PostMetadata(BaseModel):
    has_already_viewed: bool
    view_count: int
    has_already_liked: bool
    like_count: int


class AllSearchResults(BaseModel):
    profiles: List[schemas.ProfileOut]
    posts: List[PostOut]
    gig_list: List[GigListOut]
    events: List = []
    services: List = []
    campaigns: List = []
