import sqlalchemy as sa
from core.db_model_utils import Base, DateMixin, IDMixin, ModelManager, UUIDMixin
from features.post.models import HashTag
from features.profile import models
from features.sup.schemas import SupCreatedFromEnum, SupOut
from sqlalchemy.orm import Mapped, backref, mapped_column, relationship

sup_hashtags_many_to_many = sa.Table(
    "gigger_sup_hashtags",
    Base.metadata,
    sa.Column(
        "sub_uuid",
        sa.Uuid,
        sa.ForeignKey("gigger_sup_posts.uuid", ondelete="CASCADE"),
        primary_key=True,
    ),
    sa.Column(
        "hashtag_uuid",
        sa.Uuid,
        sa.ForeignKey("gigger_hashtags.uuid", ondelete="CASCADE"),
        primary_key=True,
    ),
)

sup_mentions_many_to_many = sa.Table(
    "gigger_sup_mentions",
    Base.metadata,
    sa.Column(
        "sub_uuid",
        sa.Uuid,
        sa.ForeignKey("gigger_sup_posts.uuid", ondelete="CASCADE"),
        primary_key=True,
    ),
    sa.Column(
        "profile_uuid",
        sa.Uuid,
        sa.ForeignKey("gigger_profiles.uuid", ondelete="CASCADE"),
        primary_key=True,
    ),
)
sup_like_many_to_many = sa.Table(
    "gigger_sup_likes",
    Base.metadata,
    sa.Column(
        "sup_uuid",
        sa.Uuid,
        sa.ForeignKey("gigger_sup_posts.uuid", ondelete="CASCADE"),
        primary_key=True,
    ),
    sa.Column(
        "viewer_uuid",
        sa.Uuid,
        sa.ForeignKey("gigger_profiles.uuid", ondelete="CASCADE"),
        primary_key=True,
    ),
)
sup_share_many_to_many = sa.Table(
    "gigger_sup_shares",
    Base.metadata,
    sa.Column(
        "sup_uuid",
        sa.Uuid,
        sa.ForeignKey("gigger_sup_posts.uuid", ondelete="CASCADE"),
        primary_key=True,
    ),
    sa.Column(
        "viewer_uuid",
        sa.Uuid,
        sa.ForeignKey("gigger_profiles.uuid", ondelete="CASCADE"),
        primary_key=True,
    ),
)
sup_view_many_to_many = sa.Table(
    "gigger_sup_view",
    Base.metadata,
    sa.Column(
        "sup_uuid",
        sa.Uuid,
        sa.ForeignKey("gigger_sup_posts.uuid", ondelete="CASCADE"),
        primary_key=True,
    ),
    sa.Column(
        "viewer_uuid",
        sa.Uuid,
        sa.ForeignKey("gigger_profiles.uuid", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Sup(Base, IDMixin, UUIDMixin, models.ProfileFKMixin, DateMixin, ModelManager):
    __tablename__ = "gigger_sup_posts"
    caption: Mapped[str] = mapped_column(sa.String(150))
    video_url: Mapped[str]
    thumbnail_url: Mapped[str]
    hashtags: Mapped[list["HashTag"]] = relationship(
        "HashTag",
        secondary=sup_hashtags_many_to_many,
        uselist=True,
        single_parent=True,
        backref=backref("gigger_sup_posts", lazy="selectin"),
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    tagged_profiles: Mapped[list[models.Profile]] = relationship(
        "Profile",
        secondary=sup_mentions_many_to_many,
        uselist=True,
        single_parent=True,
        backref=backref("gigger_sup_posts", lazy="selectin"),
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    lat: Mapped[float | None]
    long: Mapped[float | None]
    location: Mapped[str]
    is_membership_only: Mapped[bool]
    is_only_for_followers: Mapped[bool]
    is_already_seen: Mapped[bool] = mapped_column(default=False)
    create_from: Mapped[SupCreatedFromEnum] = mapped_column(
        default=SupCreatedFromEnum.NONE
    )

    def __repr__(self):
        return (
            f"Sup(uuid={self.uuid}, caption={self.caption}, "
            f"video_url={self.video_url}, thumbnail_url={self.thumbnail_url}, "
            f"hashtags={self.hashtags}, tagged_profiles={self.tagged_profiles}, "
            f"lat={self.lat}, long={self.long}, location={self.location}, "
            f"is_membership_only={self.is_membership_only}, "
            f"is_only_for_followers={self.is_only_for_followers})"
        )

    def to_pydantic(self) -> SupOut:
        return SupOut(
            profile_uuid=self.profile_uuid,
            uuid=self.uuid,
            caption=self.caption,
            video_url=self.video_url,
            thumbnail_url=self.thumbnail_url,
            hashtags=[hashtag.to_pydantic() for hashtag in self.hashtags],
            tagged_profiles=[profile.uuid for profile in self.tagged_profiles],
            lat=self.lat,
            long=self.long,
            location=self.location,
            is_membership_only=self.is_membership_only,
            is_only_for_followers=self.is_only_for_followers,
            tagged_profiles_details=[
                profile.to_pydantic() for profile in self.tagged_profiles
            ],
            created_at=self.created_at,
            updated_at=self.updated_at,
            is_already_seen=self.is_already_seen,
            create_from=self.create_from,
        )
