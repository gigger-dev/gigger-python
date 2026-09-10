import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID

from features.accounts import schemas as account_schemas
from pydantic import BaseModel, Field, field_validator
from pydantic.fields import FieldInfo


class NameField(BaseModel):
    name: str = Field(min_length=2, max_length=100)


class Interest(NameField):
    category: str


class InterestOut(Interest):
    uuid: UUID


class AvailabilityIn(BaseModel):
    uuid: UUID | None = None
    day: int
    start_time: datetime.time
    end_time: datetime.time

    @field_validator("day")
    def validate_day_range(cls, value):
        if not 1 <= value <= 7:
            raise ValueError("Day must be an integer between 1 and 7 (inclusive).")
        return value


class AvailabilitySearchParam(BaseModel):
    start_date: datetime.datetime
    end_date: datetime.datetime


class AvailabilityInServerSide(AvailabilityIn):
    profile_uuid: UUID


class AvailabilityOut(AvailabilityIn):
    pass


class ContactIn(BaseModel):
    uuid: UUID | None = None
    value: str
    type: str


class ContactOut(ContactIn):
    pass


class ExperiencesIn(NameField):
    uuid: UUID | None = None
    category: str


class ExperiencesOut(ExperiencesIn):
    pass


class AchievementIn(NameField):
    uuid: UUID | None = Field(default=None)
    category: str
    url: str | None


class AchievementOut(AchievementIn):
    uuid: UUID = FieldInfo.merge_field_infos(  # type: ignore
        AchievementIn.model_fields["uuid"],
        json_schema_extra={
            "schema_ui": {"readonly": True},
        },
    )  # type: ignore


class MyServicesIn(NameField):
    uuid: Optional[UUID] = Field(default=None)
    category: str


class MyServicesOut(MyServicesIn):
    uuid: UUID = FieldInfo.merge_field_infos(  # type: ignore
        MyServicesIn.model_fields["uuid"],
        json_schema_extra={
            "schema_ui": {"readonly": True},
        },
    )  # type: ignore


class EducationIn(NameField):
    uuid: UUID | None = None
    url: str | None


class EducationOut(EducationIn):
    pass


class LocationIn(BaseModel):
    address: str | None
    country: str
    city: str
    state: str


class LocationOut(LocationIn):
    uuid: UUID


class SkillIn(NameField):
    category: str


class SkillOut(SkillIn):
    uuid: UUID


class SocialLinks(Enum):
    facebook = "facebook"
    x = "x"
    instagram = "instagram"
    linkedin = "linkedin"
    github = "github"
    discord = "discord"
    telegram = "telegram"
    tiktok = "tiktok"
    youtube = "youtube"
    twitch = "twitch"

    def __str__(self) -> str:
        return self.value


class SocialLinkIn(BaseModel):
    uuid: UUID | None = None
    type: SocialLinks
    url: str


class SocialLinkOut(SocialLinkIn):
    pass


class ProfileIn(BaseModel):
    cover_media: str
    avatar_media: str
    bio: str
    availability_status: bool
    custom_phrase: str
    closing_message: str
    account_uuid: UUID
    interests: List[UUID]
    availability: List[AvailabilityIn]
    contacts: List[ContactIn]
    services: List[UUID]
    experiences: List[ExperiencesIn]
    skills: List[UUID]
    educations: List[EducationIn]
    location: LocationIn
    social_links: List[SocialLinkIn]
    achievements: List[AchievementIn]
    # in ui, skill = role, genre = interest


class ProfileUpdate(BaseModel):
    uuid: UUID  # profile_uuid
    cover_media: str | None = None
    avatar_media: str | None = None
    bio: str | None = None
    availability_status: bool | None = None
    custom_phrase: str | None = None
    closing_message: str | None = None
    interests: List[UUID] | None = None
    availability: List[AvailabilityIn] | None = None
    contacts: List[ContactIn] | None = None
    services: List[UUID] | None = None
    experiences: List[ExperiencesIn] | None = None
    skills: List[UUID] | None = None
    educations: List[EducationIn] | None = None
    location: LocationIn | None = None
    social_links: List[SocialLinkIn] | None = None
    achievements: List[AchievementIn] | None = None


class ProfileOut(BaseModel):
    cover_media: str
    avatar_media: str
    bio: str
    availability_status: bool
    custom_phrase: str
    closing_message: str

    uuid: UUID
    account_uuid: UUID
    location: LocationOut
    interests: list[InterestOut]
    availability: list[AvailabilityOut]
    contacts: list[ContactOut]
    experiences: list[ExperiencesOut]
    educations: list[EducationOut]
    skills: list[SkillOut]
    social_links: list[SocialLinkOut]
    my_services: list[MyServicesOut]
    achievements: list[AchievementOut]
    account: account_schemas.AccountOut
    is_private_profile: bool


class ProfileFewerDetailsOut(BaseModel):
    uuid: UUID
    account_uuid: UUID
    cover_media: str
    avatar_media: str
    account: account_schemas.AccountFewerDetailsOut
    is_private_profile: bool
    is_followed_back: bool | None = None
    is_follow_request_already_sent: bool | None = None
    location: LocationOut


class RelationshipMetaDataOut(BaseModel):
    is_already_requested_to_follow: bool | None = None
    is_already_following: bool


class ProfileMetaDataOut(BaseModel):
    followers_count: int
    following_count: int
    like_count: int
    view_count: int
    is_self: bool
    relationship_meta_data: Optional[RelationshipMetaDataOut]
