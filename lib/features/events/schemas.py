import datetime
from enum import Enum
from typing import Dict, List
from uuid import UUID

from core.schemas import HashTag
from features.profile.schemas import ProfileFewerDetailsOut
from features.sup.schemas import CallToAction
from pydantic import BaseModel, Field


class LineUpAndPerformerIn(BaseModel):
    profile_uuid: UUID
    start_time: datetime.datetime
    end_time: datetime.datetime

    def model_dump_with_event_uuid(self, event_uuid: UUID):
        return {
            "event_uuid": event_uuid,
            **self.model_dump(),
        }


class LineUpAndPerformerOut(LineUpAndPerformerIn):
    id: int
    event_uuid: UUID
    is_accepted: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime
    profile: ProfileFewerDetailsOut


class EventIn(BaseModel):
    name: str
    description: str
    genre: str
    hashtags: List[HashTag]
    location: str
    location_lat: float | None
    location_lon: float | None
    online_event_link: str | None
    video_or_image_url: str
    profile_uuid: UUID
    # venue: List[UUID]
    start_time: datetime.datetime
    end_time: datetime.datetime
    ticket_price: float
    currency: str = Field(
        max_length=3,
        min_length=3,
    )
    call_to_action: CallToAction
    contacts: Dict[str, str]
    social_links: Dict[str, str]
    is_membership_content: bool
    line_up_n_performers: List[LineUpAndPerformerIn]
    thumbnail_url: str


class EventUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    genre: str | None = None
    location: str | None = None
    location_lat: float | None = None
    location_lon: float | None = None
    video_or_image_url: str | None = None
    online_event_link: str | None = None
    start_time: datetime.datetime | None = None
    end_time: datetime.datetime | None = None
    ticket_price: float | None = None
    thumbnail_url: str | None = None
    currency: str | None = Field(
        default=None,
        max_length=3,
        min_length=3,
    )
    hashtags: List[HashTag] | None
    call_to_action: CallToAction | None = None
    contacts: Dict[str, str] | None = None
    social_links: Dict[str, str] | None = None
    is_membership_content: bool | None = None
    line_up_n_performers_to_remove: List[LineUpAndPerformerIn] = []
    line_up_n_performers_to_add: List[LineUpAndPerformerIn] = []


class EventOut(EventIn):
    uuid: UUID
    created_at: datetime.datetime
    updated_at: datetime.datetime
    hashtags: List[HashTag]
    line_up_n_performers: List[LineUpAndPerformerIn] = Field(
        default_factory=list, exclude=True
    )
    line_up_n_performers_out: List[LineUpAndPerformerOut]


class EventMetadata(BaseModel):
    has_already_viewed: bool
    has_already_liked: bool
    like_count: int
    response_type: int
    total_going_response: int
    going_profile: List[ProfileFewerDetailsOut]


class EventResponseDataType(Enum):
    none = (0,)
    going = (1,)
    maybe = (2,)
    interested = 3
