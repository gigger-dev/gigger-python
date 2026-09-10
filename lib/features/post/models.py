from typing import Any

import sqlalchemy as sa
from core import schemas as core_schemas
from core.db_model_utils import Base, DateMixin, IDMixin, ModelManager, UUIDMixin
from fastapi import HTTPException
from features.post import schemas
from features.profile import models
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, backref, mapped_column, relationship

post_hashtags_many_to_many = sa.Table(
    "gigger_post_hashtags",
    Base.metadata,
    sa.Column(
        "post_uuid",
        sa.Uuid,
        sa.ForeignKey("gigger_posts.uuid", ondelete="CASCADE"),
        primary_key=True,
    ),
    sa.Column(
        "hashtag_uuid",
        sa.Uuid,
        sa.ForeignKey("gigger_hashtags.uuid", ondelete="CASCADE"),
        primary_key=True,
    ),
)

post_mentions_many_to_many = sa.Table(
    "gigger_post_mentions",
    Base.metadata,
    sa.Column(
        "post_uuid",
        sa.Uuid,
        sa.ForeignKey("gigger_posts.uuid", ondelete="CASCADE"),
        primary_key=True,
    ),
    sa.Column(
        "profile_uuid",
        sa.Uuid,
        sa.ForeignKey("gigger_profiles.uuid", ondelete="CASCADE"),
        primary_key=True,
    ),
)
post_view_many_to_many = sa.Table(
    "gigger_post_viewers",
    Base.metadata,
    sa.Column(
        "post_uuid",
        sa.Uuid,
        sa.ForeignKey("gigger_posts.uuid", ondelete="CASCADE"),
        primary_key=True,
    ),
    sa.Column(
        "viewer_uuid",
        sa.Uuid,
        sa.ForeignKey("gigger_profiles.uuid", ondelete="CASCADE"),
        primary_key=True,
    ),
)

post_like_many_to_many = sa.Table(
    "gigger_post_likers",
    Base.metadata,
    sa.Column(
        "post_uuid",
        sa.Uuid,
        sa.ForeignKey("gigger_posts.uuid", ondelete="CASCADE"),
        primary_key=True,
    ),
    sa.Column(
        "liker_uuid",
        sa.Uuid,
        sa.ForeignKey("gigger_profiles.uuid", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class HashTag(Base, IDMixin, UUIDMixin, ModelManager):
    __tablename__ = "gigger_hashtags"
    name: Mapped[str] = mapped_column(sa.String(60), unique=True)

    def __repr__(self):
        return f"<HashTag {self.name}>"

    def to_pydantic(self):
        return core_schemas.HashTag(
            uuid=self.uuid,
            name=self.name,
        )


# class MemberShipType(Base, IDMixin, UUIDMixin, profile.models.ProfileFKMixin):
#     __tablename__ = "gigger_membership_types"
#     name: Mapped[str]
#     description: Mapped[str]
#     price: Mapped[float]
#     subscriptions: Mapped[list[MemberSubscription]]

# class MemberSubscription(Base, IDMixin, UUIDMixin, profile.models.ProfileFKMixin):
#     __tablename__ = "gigger_membership_subscriptions"
#     membership_type: Mapped[UUID]
#     start_date: Mapped[datetime]
#     end_date: Mapped[datetime]
#     is_active: Mapped[bool]


class Post(Base, IDMixin, UUIDMixin, models.ProfileFKMixin, ModelManager, DateMixin):
    __tablename__ = "gigger_posts"
    post_title: Mapped[str]
    caption: Mapped[str]
    music_title: Mapped[str]
    is_private: Mapped[bool]
    is_membership_only: Mapped[bool]
    is_only_for_followers: Mapped[bool]
    location: Mapped[str]
    video_url: Mapped[str]
    thumbnail_url: Mapped[str]
    hashtags: Mapped[list[HashTag]] = relationship(
        "HashTag",
        secondary=post_hashtags_many_to_many,
        uselist=True,
        single_parent=True,
        backref=backref("gigger_posts", lazy="selectin"),
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    tagged_profiles: Mapped[list[models.Profile]] = relationship(
        "Profile",
        secondary=post_mentions_many_to_many,
        uselist=True,
        single_parent=True,
        backref=backref("gigger_posts", lazy="selectin"),
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    lat: Mapped[float | None]
    long: Mapped[float | None]
    is_draft: Mapped[bool] = mapped_column(default=False)
    view_count: Mapped[int] = mapped_column(default=0, nullable=True)

    def __repr__(self):
        return f"<Post {self.post_title}>"

    def to_pydantic(self) -> schemas.PostOut:
        return schemas.PostOut(
            uuid=self.uuid,
            post_title=self.post_title,
            caption=self.caption,
            music_title=self.music_title,
            is_private=self.is_private,
            is_membership_only=self.is_membership_only,
            is_only_for_followers=self.is_only_for_followers,
            location=self.location,
            video_url=self.video_url,
            thumbnail_url=self.thumbnail_url,
            lat=self.lat,
            long=self.long,
            is_draft=self.is_draft,
            hashtags=[hashtag.to_pydantic() for hashtag in self.hashtags],
            tagged_profiles=[profile.uuid for profile in self.tagged_profiles],
            profile_uuid=self.profile_uuid,
            tagged_profiles_details=[
                profile.to_pydantic_fewer_details() for profile in self.tagged_profiles
            ],
            created_at=self.created_at,
            updated_at=self.updated_at,
            view_count=self.view_count,
        )

    @classmethod
    async def create_post(cls, db_session: AsyncSession, body: schemas.PostCreate):
        try:
            body_map = body.model_dump(
                exclude={
                    "hashtags",
                    "tagged_profiles",
                    "uuid",
                },
            )

            post = await cls.create(
                db_session=db_session,
                **body_map,
            )

            if not post:
                raise HTTPException(status_code=500, detail="Failed to create post!")
            # await post.add_hashtags(db_session=db_session, hash_tags=body.hashtags)
            await db_session.flush()
            await db_session.commit()
            await db_session.refresh(post)
            return post

        except:
            await db_session.rollback()
            raise


class PostLayout(Base, IDMixin, UUIDMixin, models.ProfileFKMixin, ModelManager):
    __tablename__ = "gigger_post_layouts"

    layout: Mapped[dict[str, Any] | None]

    def to_pydantic(self) -> schemas.PostPositionMetadata:
        return schemas.PostPositionMetadata.model_validate(self, from_attributes=True)
