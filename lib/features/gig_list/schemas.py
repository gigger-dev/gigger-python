import datetime
from typing import Annotated, Any
from uuid import UUID

from core import schemas
from features.sup.schemas import CallToAction
from pydantic import AfterValidator, BaseModel, Field, field_validator


def round_to(ndigits: int | None, /) -> AfterValidator:
    if ndigits is None:
        return AfterValidator(lambda v: v)
    return AfterValidator(lambda v: round(v, ndigits))


class GigListMedia(BaseModel):
    media_url: str
    is_video: bool

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        return cls(media_url=data["media_url"], is_video=data["is_video"])


class GigListCreate(BaseModel):
    profile_uuid: UUID
    title: str
    thumbnail_url: str
    gig_list_media: dict[int, GigListMedia] = Field(
        ..., description="Gig list media, key is int and  position of media"
    )
    description: str
    location: str
    lat: float | None = None
    long: float | None = None
    hashtags: list[schemas.HashTag]
    wage_requested: Annotated[float | None, round_to(2)]
    is_looking_for: bool
    is_performer: bool
    add_call_to_action: bool
    call_to_action: CallToAction

    @field_validator("gig_list_media")
    @classmethod
    def validate_gig_list_media(cls, gig_list_media: dict[int, GigListMedia]):
        if len(gig_list_media) > 8:
            raise ValueError("Gig list media cannot have more than 9 items")
        return gig_list_media


class GigListOut(GigListCreate):
    uuid: UUID
    created_at: datetime.datetime
    updated_at: datetime.datetime
    hashtags: list[schemas.HashTag]


class GigListUpdate(BaseModel):
    uuid: UUID
    title: str | None = None
    description: str | None = None
    location: str | None = None
    lat: float | None = None
    long: float | None = None
    hashtags: list[schemas.HashTag] | None = None
    wage_requested: Annotated[float | None, round_to(2)]
    is_looking_for: bool | None = None
    is_performer: bool | None = None
    add_call_to_action: bool | None = None
    gig_list_media: dict[int, GigListMedia] = Field(
        ..., description="Gig list media, key is int and  position of media"
    )
    thumbnail_url: str | None = None
    call_to_action: CallToAction | None = None


def gig_list_media_dto(gig_list_media: dict[int, Any]) -> dict[int, GigListMedia]:
    return {
        int(position): GigListMedia.from_dict(media)
        for position, media in gig_list_media.items()
    }


class GigListMetadata(BaseModel):
    has_already_given_star: bool
    star_count: int
    has_already_liked: bool
    like_count: int
