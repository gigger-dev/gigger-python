import datetime
from typing import List
from uuid import UUID

import sqlalchemy as sa
from core.db_model_utils import Base, DateMixin, IDMixin, ModelManager, UUIDMixin
from features.events.schemas import (
    EventOut,
    LineUpAndPerformerOut,
)
from features.post.models import HashTag
from features.profile.models import Profile, ProfileFKMixin
from features.sup.schemas import CallToAction
from sqlalchemy.orm import Mapped, backref, mapped_column, relationship

event_hashtags_many_to_many = sa.Table(
    "gigger_event_hashtags",
    Base.metadata,
    sa.Column(
        "event_uuid",
        sa.Uuid,
        sa.ForeignKey("gigger_events.uuid", ondelete="CASCADE"),
        primary_key=True,
    ),
    sa.Column(
        "hashtag_uuid",
        sa.Uuid,
        sa.ForeignKey("gigger_hashtags.uuid", ondelete="CASCADE"),
        primary_key=True,
    ),
)

event_like_many_to_many = sa.Table(
    "gigger_event_likes",
    Base.metadata,
    sa.Column(
        "event_uuid",
        sa.Uuid,
        sa.ForeignKey("gigger_events.uuid", ondelete="CASCADE"),
        primary_key=True,
    ),
    sa.Column(
        "liker_uuid",
        sa.Uuid,
        sa.ForeignKey("gigger_profiles.uuid", ondelete="CASCADE"),
        primary_key=True,
    ),
)

event_views_many_to_many = sa.Table(
    "gigger_event_views",
    Base.metadata,
    sa.Column(
        "event_uuid",
        sa.Uuid,
        sa.ForeignKey("gigger_events.uuid", ondelete="CASCADE"),
        primary_key=True,
    ),
    sa.Column(
        "viewer_uuid",
        sa.Uuid,
        sa.ForeignKey("gigger_profiles.uuid", ondelete="CASCADE"),
        primary_key=True,
    ),
)

event_response_many_to_many = sa.Table(
    "gigger_event_responses",
    Base.metadata,
    sa.Column(
        "event_uuid",
        sa.Uuid,
        sa.ForeignKey("gigger_events.uuid", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    ),
    sa.Column(
        "responder_uuid",
        sa.Uuid,
        sa.ForeignKey("gigger_profiles.uuid", ondelete="CASCADE"),
        primary_key=True,
    ),
    sa.Column(
        "response",
        sa.SmallInteger,
        nullable=False,
        index=True,
    ),
)


class LineUpAndPerformer(Base, IDMixin, ProfileFKMixin, DateMixin, ModelManager):
    __tablename__ = "gigger_events_line_ups_n_performers"
    event_uuid: Mapped[UUID] = mapped_column(
        sa.ForeignKey("gigger_events.uuid", ondelete="CASCADE"),
    )
    is_accepted: Mapped[bool] = mapped_column(
        default=False,
        server_default=sa.sql.false(),
    )
    start_time: Mapped[datetime.datetime] = mapped_column(
        sa.DateTime(timezone=True),
    )
    end_time: Mapped[datetime.datetime] = mapped_column(
        sa.DateTime(timezone=True),
    )
    event: Mapped["Event"] = relationship(
        "Event",
        back_populates="line_up_n_performers",
    )
    profile: Mapped["Profile"] = relationship(
        "Profile",
        lazy="joined",
        single_parent=True,
    )

    def to_pydantic(self) -> LineUpAndPerformerOut:
        return LineUpAndPerformerOut(
            id=self.id,
            profile_uuid=self.profile_uuid,
            event_uuid=self.event_uuid,
            is_accepted=self.is_accepted,
            created_at=self.created_at,
            updated_at=self.updated_at,
            profile=self.profile.to_pydantic_fewer_details(),
            start_time=self.start_time,
            end_time=self.end_time,
        )


# class EventVenue(Base, IDMixin, UUIDMixin, ProfileFKMixin, DateMixin, ModelManager):
#     __tablename__ = "gigger_events_venues"


class Event(Base, IDMixin, UUIDMixin, ProfileFKMixin, DateMixin, ModelManager):
    __tablename__ = "gigger_events"
    name: Mapped[str]
    description: Mapped[str]
    genre: Mapped[str]
    thumbnail_url: Mapped[str]
    video_or_image_url: Mapped[str]
    location: Mapped[str]
    location_lat: Mapped[float | None]
    location_lon: Mapped[float | None]
    online_event_link: Mapped[str | None]
    # venue: Mapped[List[UUID]]
    start_time: Mapped[datetime.datetime] = mapped_column(
        sa.DateTime(timezone=True), index=True
    )
    end_time: Mapped[datetime.datetime] = mapped_column(
        sa.DateTime(timezone=True),
    )

    ticket_price: Mapped[float]
    currency: Mapped[str] = mapped_column(sa.String(3))
    call_to_action: Mapped[dict[str, str]] = mapped_column(
        default={
            "name": None,
            "value": None,
        },
        server_default=sa.text('\'{"name": null, "value": null}\''),
    )
    is_membership_content: Mapped[bool] = mapped_column(default=False)
    contacts: Mapped[dict[str, str] | None] = mapped_column(
        default=None,
        server_default=sa.null(),
    )
    social_links: Mapped[dict[str, str] | None] = mapped_column(
        default=None,
        server_default=sa.null(),
    )
    line_up_n_performers: Mapped[List[LineUpAndPerformer]] = relationship(
        LineUpAndPerformer,
        back_populates="event",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    hashtags: Mapped[list[HashTag]] = relationship(
        "HashTag",
        secondary=event_hashtags_many_to_many,
        uselist=True,
        single_parent=True,
        backref=backref("gigger_events", lazy="selectin"),
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def to_pydantic(self) -> EventOut:
        return EventOut(
            uuid=self.uuid,
            name=self.name,
            description=self.description,
            genre=self.genre,
            thumbnail_url=self.thumbnail_url,
            video_or_image_url=self.video_or_image_url,
            location=self.location,
            location_lat=self.location_lat,
            location_lon=self.location_lon,
            online_event_link=self.online_event_link,
            start_time=self.start_time,
            end_time=self.end_time,
            currency=self.currency,
            call_to_action=CallToAction.model_validate(self.call_to_action),
            contacts=self.contacts if self.contacts else {},
            social_links=self.social_links if self.social_links else {},
            is_membership_content=self.is_membership_content,
            line_up_n_performers=[],
            line_up_n_performers_out=[
                line.to_pydantic() for line in self.line_up_n_performers
            ],
            hashtags=[hashtag.to_pydantic() for hashtag in self.hashtags],
            # venue=self.venue,
            ticket_price=self.ticket_price,
            created_at=self.created_at,
            updated_at=self.updated_at,
            profile_uuid=self.profile_uuid,
        )
