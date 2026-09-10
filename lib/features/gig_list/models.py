from typing import List

import sqlalchemy as sa
from core import schemas
from core.db_model_utils import Base, DateMixin, IDMixin, ModelManager, UUIDMixin
from features.gig_list.schemas import GigListMedia, GigListOut, gig_list_media_dto
from features.post.models import HashTag
from features.profile.models import ProfileFKMixin
from features.sup.schemas import CallToAction
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, backref, mapped_column, relationship

gig_list_hashtags_many_to_many = sa.Table(
    "gigger_gig_list_hashtags",
    Base.metadata,
    sa.Column(
        "gig_list_uuid",
        sa.Uuid,
        sa.ForeignKey("gigger_gig_lists.uuid", ondelete="CASCADE"),
        primary_key=True,
    ),
    sa.Column(
        "hashtag_uuid",
        sa.Uuid,
        sa.ForeignKey("gigger_hashtags.uuid", ondelete="CASCADE"),
        primary_key=True,
    ),
)
gig_list_stars_many_to_many = sa.Table(
    "gigger_gig_list_stars",
    Base.metadata,
    sa.Column(
        "gig_list_uuid",
        sa.Uuid,
        sa.ForeignKey("gigger_gig_lists.uuid", ondelete="CASCADE"),
        primary_key=True,
    ),
    sa.Column(
        "viewer_uuid",
        sa.Uuid,
        sa.ForeignKey("gigger_profiles.uuid", ondelete="CASCADE"),
        primary_key=True,
    ),
)

gig_list_like_many_to_many = sa.Table(
    "gigger_gig_list_likes",
    Base.metadata,
    sa.Column(
        "gig_list_uuid",
        sa.Uuid,
        sa.ForeignKey("gigger_gig_lists.uuid", ondelete="CASCADE"),
        primary_key=True,
    ),
    sa.Column(
        "liker_uuid",
        sa.Uuid,
        sa.ForeignKey("gigger_profiles.uuid", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class GigList(Base, IDMixin, UUIDMixin, ProfileFKMixin, DateMixin, ModelManager):
    __tablename__ = "gigger_gig_lists"
    title: Mapped[str]
    description: Mapped[str]
    location: Mapped[str]
    lat: Mapped[float | None]
    long: Mapped[float | None]
    thumbnail_url: Mapped[str]
    gig_list_media: Mapped[dict[int, GigListMedia]]
    hashtags: Mapped[list["HashTag"]] = relationship(
        "HashTag",
        secondary=gig_list_hashtags_many_to_many,
        uselist=True,
        single_parent=True,
        backref=backref("gigger_gig_lists", lazy="selectin"),
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    wage_requested: Mapped[float | None] = mapped_column(
        sa.Numeric(10, 2), nullable=True
    )
    is_looking_for: Mapped[bool]
    is_performer: Mapped[bool]
    add_call_to_action: Mapped[bool]
    call_to_action: Mapped[dict[str, str]] = mapped_column(
        default={
            "name": None,
            "value": None,
        },
        server_default=sa.text('\'{"name": null, "value": null}\''),
    )

    def to_pydantic(self) -> GigListOut:
        return GigListOut(
            uuid=self.uuid,
            title=self.title,
            description=self.description,
            location=self.location,
            lat=self.lat,
            long=self.long,
            wage_requested=self.wage_requested,
            is_looking_for=self.is_looking_for,
            is_performer=self.is_performer,
            add_call_to_action=self.add_call_to_action,
            profile_uuid=self.profile_uuid,
            hashtags=[hashtag.to_pydantic() for hashtag in self.hashtags],
            thumbnail_url=self.thumbnail_url,
            gig_list_media=gig_list_media_dto(self.gig_list_media),
            created_at=self.created_at,
            updated_at=self.updated_at,
            call_to_action=CallToAction.model_validate(
                self.call_to_action,
            ),
        )

    async def add_hashtags(
        self,
        db_session: AsyncSession,
        hash_tags: List[schemas.HashTag],
    ):
        for hash_tag in hash_tags:
            if not hash_tag.uuid:
                hash_tag_created = await HashTag.create_if_not_exist(
                    db_session=db_session, **hash_tag.model_dump(exclude_none=True)
                )
                if hash_tag_created:
                    self.hashtags.append(hash_tag_created)
                else:
                    hash_tag_search = await HashTag.get(
                        db_session=db_session, name=hash_tag.name
                    )
                    if hash_tag_search:
                        self.hashtags.append(hash_tag_search)
            else:
                if hash_tag.uuid in [uuids for uuids in self.hashtags]:
                    continue
                get_has_tag = await HashTag.get(
                    db_session=db_session, uuid=hash_tag.uuid
                )
                if get_has_tag:
                    self.hashtags.append(get_has_tag)

    def __repr__(self):
        return f"<GigList {self.title}>"
