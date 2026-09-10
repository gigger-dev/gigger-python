import datetime
from typing import List
from uuid import UUID

import sqlalchemy as sa
from core.db_model_utils import Base, DateMixin, IDMixin, ModelManager, UUIDMixin
from core.global_import import AsyncSession
from fastapi import HTTPException, status
from features.accounts import models as a_models
from features.profile import schemas as profile_schemas
from sqlalchemy.orm import Mapped, backref, mapped_column, relationship


def time_now():
    datetime.datetime.now(datetime.timezone.utc)


user_interests_many_to_many = sa.Table(
    "gigger_profile_interests",
    Base.metadata,
    sa.Column(
        "profile_uuid",
        sa.Uuid,
        sa.ForeignKey("gigger_profiles.uuid", ondelete="CASCADE"),
        primary_key=True,
    ),
    sa.Column(
        "interest_uuid",
        sa.Uuid,
        sa.ForeignKey("gigger_interests.uuid", ondelete="CASCADE"),
        primary_key=True,
    ),
)

profile_skill_many_to_many = sa.Table(
    "gigger_profile_skills",
    Base.metadata,
    sa.Column(
        "profile_uuid",
        sa.Uuid,
        sa.ForeignKey("gigger_profiles.uuid", ondelete="CASCADE"),
        primary_key=True,
    ),
    sa.Column(
        "skill_uuid",
        sa.Uuid,
        sa.ForeignKey("gigger_skills.uuid", ondelete="CASCADE"),
        primary_key=True,
    ),
)

profile_services_many_to_many = sa.Table(
    "gigger_profile_services",
    Base.metadata,
    sa.Column(
        "profile_uuid",
        sa.Uuid,
        sa.ForeignKey("gigger_profiles.uuid", ondelete="CASCADE"),
        primary_key=True,
    ),
    sa.Column(
        "service_uuid",
        sa.Uuid,
        sa.ForeignKey("gigger_my_services.uuid", ondelete="CASCADE"),
        primary_key=True,
    ),
)

profile_followers_many_to_many = sa.Table(
    "gigger_profile_followers",
    Base.metadata,
    sa.Column(
        "profile_uuid",
        sa.Uuid,
        sa.ForeignKey("gigger_profiles.uuid", ondelete="CASCADE"),
        primary_key=True,
    ),
    sa.Column(
        "follower_uuid",
        sa.Uuid,
        sa.ForeignKey("gigger_profiles.uuid", ondelete="CASCADE"),
        primary_key=True,
    ),
    sa.Column(
        "created_at",
        sa.DateTime(timezone=True),
        nullable=False,
        default=time_now,
        server_default=sa.func.now(),
    ),
)


follower_request_many_to_many = sa.Table(
    "gigger_follower_requests",
    Base.metadata,
    sa.Column(
        "profile_uuid",
        sa.Uuid,
        sa.ForeignKey("gigger_profiles.uuid", ondelete="CASCADE"),
        primary_key=True,
    ),
    sa.Column(
        "follower_uuid",
        sa.Uuid,
        sa.ForeignKey("gigger_profiles.uuid", ondelete="CASCADE"),
        primary_key=True,
    ),
)

profile_viewer_many_to_many = sa.Table(
    "gigger_profile_viewers",
    Base.metadata,
    sa.Column(
        "profile_uuid",
        sa.Uuid,
        sa.ForeignKey("gigger_profiles.uuid", ondelete="CASCADE"),
        primary_key=True,
    ),
    sa.Column(
        "viewer_uuid",
        sa.Uuid,
        sa.ForeignKey("gigger_profiles.uuid", ondelete="CASCADE"),
        primary_key=True,
    ),
)

profile_like_many_to_many = sa.Table(
    "gigger_profile_likes",
    Base.metadata,
    sa.Column(
        "profile_uuid",
        sa.Uuid,
        sa.ForeignKey("gigger_profiles.uuid", ondelete="CASCADE"),
        primary_key=True,
    ),
    sa.Column(
        "liker_uuid",
        sa.Uuid,
        sa.ForeignKey("gigger_profiles.uuid", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Interest(Base, IDMixin, UUIDMixin, ModelManager):
    __tablename__ = "gigger_interests"

    name: Mapped[str] = mapped_column(sa.String(60), unique=True)
    category: Mapped[str] = mapped_column(index=True)

    def __repr__(self):
        return f"Interest(name={self.name}, category={self.category})"

    @classmethod
    async def list_interests_by_uuids(cls, db_session: AsyncSession, uuids: List[UUID]):
        stmt = sa.select(Interest).where(
            Interest.uuid.in_(set(uuids)),
        )
        result = await db_session.scalars(stmt)
        return result.all()

    def to_pydantic(self) -> profile_schemas.InterestOut:
        return profile_schemas.InterestOut.model_validate(self, from_attributes=True)


class Profile(Base, IDMixin, UUIDMixin, ModelManager, DateMixin):
    __tablename__ = "gigger_profiles"

    account_uuid: Mapped[UUID] = mapped_column(
        sa.ForeignKey("gigger_accounts.uuid", ondelete="CASCADE"), unique=True
    )
    account: Mapped["a_models.Account"] = relationship(
        "Account",
        uselist=False,
        back_populates="profile",
        lazy="selectin",
    )
    cover_media: Mapped[str]
    avatar_media: Mapped[str]

    location: Mapped["ProfileLocation"] = relationship(
        "ProfileLocation",
        uselist=False,
        lazy="selectin",
        back_populates="profile",
        single_parent=True,
    )
    # followers: Mapped[list["Profile"]] = relationship(
    #     "Profile",
    #     secondary=profile_followers_many_to_many,
    #     primaryjoin="Profile.uuid == gigger_profile_followers.profile_uuid",
    #     secondaryjoin="Profile.uuid == gigger_profile_followers.follower_uuid",
    #     uselist=True,
    #     lazy="noload",
    # )
    bio: Mapped[str]
    availability_status: Mapped[bool]  # just store on/off

    availability: Mapped[list["Availability"]] = relationship(
        "Availability",
        uselist=True,
        lazy="selectin",
        backref=backref("gigger_profiles", lazy="selectin"),
        cascade="all, delete-orphan",
        single_parent=True,
    )
    is_private_profile: Mapped[bool] = mapped_column(default=False)
    custom_phrase: Mapped[str]
    closing_message: Mapped[str]
    contacts: Mapped[list["Contact"]] = relationship(
        "Contact",
        uselist=True,
        lazy="selectin",
        backref=backref("gigger_profiles", lazy="selectin"),
        cascade="all, delete-orphan",
        single_parent=True,
    )
    interests: Mapped[list["Interest"]] = relationship(
        "Interest",
        secondary=user_interests_many_to_many,
        uselist=True,
        lazy="selectin",
        backref=backref("gigger_profiles", lazy="selectin"),
        cascade="all, delete-orphan",
        single_parent=True,
    )
    my_services: Mapped[list["MyServices"]] = relationship(
        "MyServices",
        uselist=True,
        secondary=profile_services_many_to_many,
        lazy="selectin",
        backref=backref("gigger_profiles", lazy="selectin"),
        cascade="all, delete-orphan",
        single_parent=True,
    )
    experiences: Mapped[list["Experiences"]] = relationship(
        "Experiences",
        uselist=True,
        lazy="selectin",
        backref=backref("gigger_profiles", lazy="selectin"),
        cascade="all, delete-orphan",
        single_parent=True,
    )
    educations: Mapped[list["Education"]] = relationship(
        "Education",
        uselist=True,
        lazy="selectin",
        backref=backref("gigger_profiles", lazy="selectin"),
        cascade="all, delete-orphan",
        single_parent=True,
    )

    social_links: Mapped[list["SocialLink"]] = relationship(
        "SocialLink",
        uselist=True,
        lazy="selectin",
        backref=backref("gigger_profiles", lazy="selectin"),
        cascade="all, delete-orphan",
        single_parent=True,
    )
    achievements: Mapped[list["Achievement"]] = relationship(
        "Achievement",
        uselist=True,
        lazy="selectin",
        backref=backref("gigger_profiles", lazy="selectin"),
        cascade="all, delete-orphan",
        single_parent=True,
    )

    skills: Mapped[list["Skill"]] = relationship(
        "Skill",
        secondary=profile_skill_many_to_many,
        uselist=True,
        lazy="selectin",
        backref=backref("gigger_profiles", lazy="selectin"),
        cascade="all, delete-orphan",
        single_parent=True,
    )

    def __repr__(self):
        return f"Profile(uuid={self.uuid}, account_uuid={self.account_uuid})"

    async def add_interests(self, db_session: AsyncSession, interest_uuids: List[UUID]):
        interests = await Interest.list_interests_by_uuids(
            db_session=db_session, uuids=interest_uuids
        )
        # removed if interest is not in the list.
        for i in self.interests:
            if i not in interests:
                self.interests.remove(i)

        self.interests.clear()
        self.interests.extend(interests)
        await db_session.flush()
        await db_session.commit()
        await db_session.refresh(self)

    async def remove_interests(
        self, db_session: AsyncSession, interest_uuids: List[UUID]
    ):
        interests = await Interest.list_interests_by_uuids(
            db_session=db_session, uuids=interest_uuids
        )
        self.interests = [
            interest for interest in self.interests if interest not in interests
        ]
        await db_session.flush()
        await db_session.commit()
        await db_session.refresh(self)

    async def add_skills(self, db_session: AsyncSession, skill_uuids: List[UUID]):
        skills = await Skill.list_skills_by_uuids(
            db_session=db_session, uuids=skill_uuids
        )
        # removed if skill is not in the list.
        for i in self.skills:
            if i not in skills:
                self.skills.remove(i)

        self.skills.clear()
        self.skills.extend(skills)
        await db_session.flush()
        await db_session.commit()
        await db_session.refresh(self)

    async def remove_skills(self, db_session: AsyncSession, skill_uuids: List[UUID]):
        skills = await Skill.list_skills_by_uuids(
            db_session=db_session, uuids=skill_uuids
        )
        self.skills = [skill for skill in self.skills if skill not in skills]
        await db_session.flush()
        await db_session.commit()
        await db_session.refresh(self)

    async def add_my_services(
        self, db_session: AsyncSession, service_uuids: List[UUID]
    ):
        services = await MyServices.list_my_services_by_uuids(
            db_session=db_session, uuids=service_uuids
        )
        # removed if service is not in the list.
        for i in self.my_services:
            if i not in services:
                self.my_services.remove(i)
        self.my_services.clear()
        self.my_services.extend(services)
        await db_session.flush()
        await db_session.commit()
        await db_session.refresh(self)

    async def remove_my_services(
        self, db_session: AsyncSession, service_uuids: List[UUID]
    ):
        services = await MyServices.list_my_services_by_uuids(
            db_session=db_session, uuids=service_uuids
        )
        self.my_services = [
            service for service in self.my_services if service not in services
        ]
        await db_session.flush()
        await db_session.commit()
        await db_session.refresh(self)

    async def add_contacts(
        self, db_session: AsyncSession, contact_in_list: List[profile_schemas.ContactIn]
    ):
        # removed if contact is not in the list.
        for contact in self.contacts:
            if contact not in contact_in_list:
                self.contacts.remove(contact)
        for contact_in in contact_in_list:
            if contact_in.uuid:
                continue
            else:
                contact = await Contact.create_if_not_exist(
                    db_session=db_session,
                    **contact_in.model_dump(),
                    profile_uuid=self.uuid,
                )
                if contact and contact.id not in [
                    contact.id for contact in self.contacts
                ]:
                    self.contacts.append(contact)

        await db_session.flush()
        await db_session.commit()
        await db_session.refresh(self)

    async def add_education(
        self,
        db_session: AsyncSession,
        education_in_list: List[profile_schemas.EducationIn],
    ):
        # removed if education is not in the list.
        for education in self.educations:
            if education not in education_in_list:
                self.educations.remove(education)
        for education_in in education_in_list:
            if education_in.uuid:
                continue
            else:
                education = await Education.create_if_not_exist(
                    db_session=db_session,
                    **education_in.model_dump(),
                    profile_uuid=self.uuid,
                )
                if education and education.id not in [
                    education.id for education in self.educations
                ]:
                    self.educations.append(education)

        await db_session.flush()
        await db_session.commit()
        await db_session.refresh(self)

    async def add_experience(
        self,
        db_session: AsyncSession,
        experience_in_list: List[profile_schemas.ExperiencesIn],
    ):
        # removed if experience is not in the list.
        for experience in self.experiences:
            if experience not in experience_in_list:
                self.experiences.remove(experience)
        for experience_in in experience_in_list:
            if experience_in.uuid:
                continue
            else:
                experience = await Experiences.create_if_not_exist(
                    db_session=db_session,
                    **experience_in.model_dump(),
                    profile_uuid=self.uuid,
                )
                if experience and experience.id not in [
                    experience.id for experience in self.experiences
                ]:
                    self.experiences.append(experience)

        await db_session.flush()
        await db_session.commit()
        await db_session.refresh(self)

    async def add_social_links(
        self,
        db_session: AsyncSession,
        social_links_in_list: List[profile_schemas.SocialLinkIn],
    ):
        # removed if social_link is not in the list.
        for social_link in self.social_links:
            if social_link not in social_links_in_list:
                self.social_links.remove(social_link)
        for social_link_in in social_links_in_list:
            if social_link_in.uuid:
                continue
            else:
                social_link = await SocialLink.create_if_not_exist(
                    db_session=db_session,
                    **social_link_in.model_dump(),
                    profile_uuid=self.uuid,
                )
                if social_link and social_link.id not in [
                    social_link.id for social_link in self.social_links
                ]:
                    self.social_links.append(social_link)

        await db_session.flush()
        await db_session.commit()
        await db_session.refresh(self)

    async def add_availability(
        self,
        db_session: AsyncSession,
        availability_in_list: List[profile_schemas.AvailabilityIn],
    ):
        # removed if availability is not in the list.
        for availability in self.availability:
            if availability.uuid not in [
                availability_in_list.uuid
                for availability_in_list in availability_in_list
            ]:
                self.availability.remove(availability)
        for availability_in in availability_in_list:
            if availability_in.uuid:
                continue
            else:
                availability = await Availability.create_if_not_exist(
                    db_session=db_session,
                    **availability_in.model_dump(),
                    profile_uuid=self.uuid,
                )
                if availability and availability.id not in [
                    availability.id for availability in self.availability
                ]:
                    self.availability.append(availability)

        await db_session.flush()
        await db_session.commit()
        await db_session.refresh(self)

    async def add_location(
        self, db_session: AsyncSession, location_in: profile_schemas.LocationIn
    ):
        location = await ProfileLocation.get(
            db_session=db_session,
            profile_uuid=self.uuid,
        )
        if location:
            await location.update(
                db_session=db_session,
                **location_in.model_dump(),
            )
        else:
            await ProfileLocation.create(
                db_session=db_session,
                **location_in.model_dump(),
                profile_uuid=self.uuid,
            )
        await db_session.flush()
        await db_session.commit()
        await db_session.refresh(self)

    async def add_achievements(
        self,
        db_session: AsyncSession,
        achievements_in_list: List[profile_schemas.AchievementIn],
    ):
        # removed if achievement is not in the list.
        for achievement in self.achievements:
            if achievement.name not in [
                achievement.name for achievement in achievements_in_list
            ]:
                self.achievements.remove(achievement)
                await db_session.flush()
                await db_session.commit()
                await db_session.refresh(self)
        # TODO: refactor.
        for achievement_in in achievements_in_list:
            stmt = None
            if achievement_in.uuid:
                continue
            if db_session.bind.dialect.name == "postgresql":
                import sqlalchemy.dialects.postgresql as pa

                # PostgreSQL: Use `on_conflict_do_nothing`
                stmt = (
                    pa.insert(Achievement)
                    .values(
                        name=achievement_in.name,
                        category=achievement_in.category,
                        url=achievement_in.url,
                        uuid=achievement_in.uuid,
                        profile_uuid=self.uuid,
                    )
                    .on_conflict_do_nothing(
                        index_elements=["name"]  # Field(s) that should be unique
                    )
                )
            elif db_session.bind.dialect.name == "sqlite":
                # SQLite: Use `INSERT OR IGNORE`
                stmt = sa.text(
                    """
                    INSERT OR IGNORE INTO gigger_achievements (name, category, url, uuid, profile_uuid)
                    VALUES (:name, :category, :url, :uuid, :profile_uuid)
                    """
                ).bindparams(
                    name=achievement_in.name,
                    category=achievement_in.category,
                    url=achievement_in.url,
                    uuid=achievement_in.uuid,
                    profile_uuid=self.uuid,
                )

            if stmt is not None:
                await db_session.execute(stmt)
                await db_session.commit()

        # for achievement_in in achievements_in_list:
        #     if achievement_in.uuid:
        #         continue
        #     else:
        #         achievement = await Achievement.create_if_not_exist(
        #             db_session=db_session,
        #             **achievement_in.model_dump(),
        #             profile_uuid=self.uuid,
        #         )
        #         # if achievement and achievement.id not in [
        #         #     achievement.id for achievement in self.achievements
        #         # ]:
        #         #     self.achievements.append(achievement)

        await db_session.refresh(self)

    def to_pydantic(self) -> profile_schemas.ProfileOut:
        return profile_schemas.ProfileOut(
            account_uuid=self.account_uuid,
            cover_media=self.cover_media,
            avatar_media=self.avatar_media,
            bio=self.bio,
            availability_status=self.availability_status,
            custom_phrase=self.custom_phrase,
            closing_message=self.closing_message,
            uuid=self.uuid,
            location=self.location.to_pydantic(),
            interests=[interest.to_pydantic() for interest in self.interests],
            availability=[
                availability.to_pydantic() for availability in self.availability
            ],
            contacts=[contact.to_pydantic() for contact in self.contacts],
            experiences=[experience.to_pydantic() for experience in self.experiences],
            educations=[education.to_pydantic() for education in self.educations],
            skills=[skill.to_pydantic() for skill in self.skills],
            social_links=[
                social_link.to_pydantic() for social_link in self.social_links
            ],
            my_services=[my_service.to_pydantic() for my_service in self.my_services],
            achievements=[
                achievement.to_pydantic() for achievement in self.achievements
            ]
            if self.achievements
            else [],
            account=self.account.to_pydantic(),
            is_private_profile=self.is_private_profile,
        )

    def to_pydantic_fewer_details(
        self,
        is_followed_back: bool | None = None,
        is_follow_request_already_sent: bool | None = None,
    ) -> profile_schemas.ProfileFewerDetailsOut:
        return profile_schemas.ProfileFewerDetailsOut(
            uuid=self.uuid,
            account_uuid=self.account_uuid,
            cover_media=self.cover_media,
            avatar_media=self.avatar_media,
            account=self.account.to_pydantic_fewer_details(),
            is_private_profile=self.is_private_profile,
            is_followed_back=is_followed_back,
            location=self.location.to_pydantic(),
            is_follow_request_already_sent=is_follow_request_already_sent,
        )

    @classmethod
    async def create_profile(
        cls,
        db_session: AsyncSession,
        profile_in: profile_schemas.ProfileIn,
    ):
        profile = await Profile.create(
            db_session=db_session,
            account_uuid=profile_in.account_uuid,
            cover_media=profile_in.cover_media,
            avatar_media=profile_in.avatar_media,
            bio=profile_in.bio,
            availability_status=profile_in.availability_status,
            custom_phrase=profile_in.custom_phrase,
            closing_message=profile_in.closing_message,
        )
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create profile.",
            )

        if profile_in.interests:
            await profile.add_interests(
                db_session=db_session, interest_uuids=profile_in.interests
            )

        if profile_in.skills:
            await profile.add_skills(
                db_session=db_session, skill_uuids=profile_in.skills
            )

        if profile_in.services:
            await profile.add_my_services(
                db_session=db_session, service_uuids=profile_in.services
            )
        if profile_in.educations:
            for edu in profile_in.educations:
                await Education.create_if_not_exist(
                    db_session=db_session,
                    profile_uuid=profile.uuid,
                    name=edu.name,
                    url=edu.url,
                )
        if profile_in.experiences:
            for exp in profile_in.experiences:
                await Experiences.create_if_not_exist(
                    db_session=db_session,
                    profile_uuid=profile.uuid,
                    name=exp.name,
                    category=exp.category,
                )

        if profile_in.social_links:
            for link in profile_in.social_links:
                await SocialLink.create_if_not_exist(
                    db_session=db_session,
                    profile_uuid=profile.uuid,
                    type=link.type,
                    url=link.url,
                )
        if profile_in.contacts:
            for contact in profile_in.contacts:
                await Contact.create_if_not_exist(
                    db_session=db_session,
                    profile_uuid=profile.uuid,
                    value=contact.value,
                    type=contact.type,
                )
        if profile_in.availability:
            for availability in profile_in.availability:
                await Availability.create_if_not_exist(
                    db_session=db_session,
                    profile_uuid=profile.uuid,
                    start_time=availability.start_time,
                    end_time=availability.end_time,
                    day=availability.day,
                )
        if profile_in.location:
            await ProfileLocation.create_if_not_exist(
                db_session=db_session,
                profile_uuid=profile.uuid,
                city=profile_in.location.city,
                state=profile_in.location.state,
                country=profile_in.location.country,
                address=profile_in.location.address,
            )
        if profile_in.achievements:
            for achievement in profile_in.achievements:
                await Achievement.insert_or_ignore(
                    db_session=db_session,
                    profile_uuid=profile.uuid,
                    name=achievement.name,
                    category=achievement.category,
                    url=achievement.url,
                )
        await db_session.flush()
        await db_session.commit()
        await db_session.refresh(profile)

        profile = await db_session.scalar(
            sa.select(cls)
            .where(cls.uuid == profile.uuid)
            .options(sa.orm.selectinload(cls.achievements))
        )
        return profile

    async def get_followers(self, db_session: AsyncSession):
        stmt = (
            sa.select(Profile)
            .join(
                profile_followers_many_to_many,
                profile_followers_many_to_many.c.profile_uuid == Profile.uuid,
            )
            .filter(
                profile_followers_many_to_many.c.profile_uuid == self.uuid,
            )
        )
        result = await db_session.scalars(stmt)
        return [result.to_pydantic() for result in result.all()]

    async def get_following(self, db_session: AsyncSession):
        stmt = (
            sa.select(Profile)
            .join(
                profile_followers_many_to_many,
                profile_followers_many_to_many.c.follower_uuid == Profile.uuid,
            )
            .filter(
                profile_followers_many_to_many.c.follower_uuid == self.uuid,
            )
        )
        result = await db_session.scalars(stmt)
        return [result.to_pydantic() for result in result.all()]

    @classmethod
    async def update_profile(
        cls, db_session: AsyncSession, profile_update: profile_schemas.ProfileUpdate
    ):
        profile = await cls.get(db_session=db_session, uuid=profile_update.uuid)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found"
            )
        if profile_update.cover_media:
            profile.cover_media = profile_update.cover_media
        if profile_update.avatar_media:
            profile.avatar_media = profile_update.avatar_media
        if profile_update.bio:
            profile.bio = profile_update.bio
        if profile_update.availability_status is not None:
            profile.availability_status = profile_update.availability_status
        if profile_update.custom_phrase:
            profile.custom_phrase = profile_update.custom_phrase
        if profile_update.closing_message:
            profile.closing_message = profile_update.closing_message
        if profile_update.interests:
            await profile.add_interests(
                db_session=db_session, interest_uuids=profile_update.interests
            )
        if profile_update.skills:
            await profile.add_skills(
                db_session=db_session, skill_uuids=profile_update.skills
            )
        if profile_update.services:
            await profile.add_my_services(
                db_session=db_session, service_uuids=profile_update.services
            )
        if profile_update.educations:
            await profile.add_education(db_session, profile_update.educations)
        if profile_update.experiences:
            await profile.add_experience(db_session, profile_update.experiences)
        if profile_update.social_links:
            await profile.add_social_links(db_session, profile_update.social_links)
        if profile_update.contacts:
            await profile.add_contacts(db_session, profile_update.contacts)
        if profile_update.availability:
            await profile.add_availability(db_session, profile_update.availability)
        if profile_update.location:
            await profile.add_location(db_session, profile_update.location)
        if profile_update.achievements:
            await profile.add_achievements(db_session, profile_update.achievements)

        await db_session.flush()
        await db_session.commit()
        await db_session.refresh(profile)
        return profile


class ProfileFKMixin:
    profile_uuid: Mapped[UUID] = mapped_column(
        sa.ForeignKey("gigger_profiles.uuid", ondelete="CASCADE"),
    )


class Availability(Base, IDMixin, UUIDMixin, ModelManager, ProfileFKMixin):
    __tablename__ = "gigger_availability"
    start_time: Mapped[datetime.time]
    end_time: Mapped[datetime.time]
    day: Mapped[int]

    def to_pydantic(self) -> profile_schemas.AvailabilityOut:
        return profile_schemas.AvailabilityOut.model_validate(
            self, from_attributes=True
        )


# one_to_many
class Contact(Base, IDMixin, UUIDMixin, ModelManager, ProfileFKMixin):
    __tablename__ = "gigger_contacts"
    value: Mapped[str]
    type: Mapped[str]

    def to_pydantic(self) -> profile_schemas.ContactOut:
        return profile_schemas.ContactOut.model_validate(self, from_attributes=True)


class MyServices(Base, IDMixin, UUIDMixin, ModelManager):
    __tablename__ = "gigger_my_services"
    name: Mapped[str] = mapped_column(sa.String(60), unique=True)
    category: Mapped[str]

    def to_pydantic(self) -> profile_schemas.MyServicesOut:
        return profile_schemas.MyServicesOut.model_validate(self, from_attributes=True)

    @classmethod
    async def list_my_services_by_uuids(
        cls, db_session: AsyncSession, uuids: List[UUID]
    ):
        stmt = sa.select(MyServices).where(
            MyServices.uuid.in_(set(uuids)),
        )
        result = await db_session.scalars(stmt)
        return result.all()


class Experiences(Base, IDMixin, UUIDMixin, ModelManager, ProfileFKMixin):
    __tablename__ = "gigger_experiences"
    name: Mapped[str]
    category: Mapped[str | None]

    def to_pydantic(self) -> profile_schemas.ExperiencesOut:
        return profile_schemas.ExperiencesOut.model_validate(self, from_attributes=True)


class Skill(Base, IDMixin, UUIDMixin, ModelManager):
    __tablename__ = "gigger_skills"
    name: Mapped[str] = mapped_column(sa.String(60), unique=True)
    category: Mapped[str]

    def to_pydantic(self) -> profile_schemas.SkillOut:
        return profile_schemas.SkillOut.model_validate(self, from_attributes=True)

    @classmethod
    async def list_skills_by_uuids(cls, db_session: AsyncSession, uuids: List[UUID]):
        stmt = sa.select(Skill).where(
            Skill.uuid.in_(set(uuids)),
        )
        result = await db_session.scalars(stmt)
        return result.all()


class Education(Base, IDMixin, UUIDMixin, ModelManager, ProfileFKMixin):
    __tablename__ = "gigger_education"
    name: Mapped[str]
    url: Mapped[str | None]

    def to_pydantic(self) -> profile_schemas.EducationOut:
        return profile_schemas.EducationOut.model_validate(self, from_attributes=True)


class SocialLink(Base, IDMixin, UUIDMixin, ModelManager, ProfileFKMixin):
    __tablename__ = "gigger_social_links"
    url: Mapped[str]
    type: Mapped[profile_schemas.SocialLinks]

    def to_pydantic(self) -> profile_schemas.SocialLinkOut:
        return profile_schemas.SocialLinkOut.model_validate(self, from_attributes=True)


class ProfileLocation(Base, IDMixin, UUIDMixin, ModelManager, ProfileFKMixin):
    __tablename__ = "gigger_profile_locations"
    address: Mapped[str | None]
    country: Mapped[str]
    city: Mapped[str]
    state: Mapped[str]
    profile: Mapped["Profile"] = relationship(
        "Profile",
        back_populates="location",
    )

    def __repr__(self) -> str:
        return f"ProfileLocation(address={self.address}, country={self.country}, city={self.city})"

    def to_pydantic(self) -> profile_schemas.LocationOut:
        return profile_schemas.LocationOut.model_validate(self, from_attributes=True)


class Achievement(Base, IDMixin, UUIDMixin, ModelManager, ProfileFKMixin):
    __tablename__ = "gigger_achievements"
    name: Mapped[str] = mapped_column(sa.String(60), unique=True)
    category: Mapped[str | None]
    url: Mapped[str | None]

    def to_pydantic(self) -> profile_schemas.AchievementOut:
        return profile_schemas.AchievementOut.model_validate(self, from_attributes=True)

    def __repr__(self) -> str:
        return (
            f"Achievement(name={self.name}, category={self.category}, url={self.url})"
        )

    @classmethod
    async def insert_or_ignore(cls, db_session: AsyncSession, **kwargs):
        achievement_in = profile_schemas.AchievementIn(**kwargs)
        if db_session.bind.dialect.name == "postgresql":
            import sqlalchemy.dialects.postgresql as pa

            # PostgreSQL: Use `on_conflict_do_nothing`
            stmt = (
                pa.insert(Achievement)
                .values(
                    name=achievement_in.name,
                    category=achievement_in.category,
                    url=achievement_in.url,
                    profile_uuid=kwargs["profile_uuid"],
                )
                .on_conflict_do_nothing(
                    index_elements=["name"]  # Field(s) that should be unique
                )
            )
            result = await db_session.scalar(stmt.returning(Achievement))
            return result
        elif db_session.bind.dialect.name == "sqlite":
            from sqlalchemy.dialects import sqlite as sa

            stmt = (
                sa.insert(Achievement)
                .values(
                    name=achievement_in.name,
                    category=achievement_in.category,
                    url=achievement_in.url,
                    profile_uuid=kwargs["profile_uuid"],
                )
                .on_conflict_do_nothing(
                    index_elements=["name"]  # Field(s) that should be unique
                )
            )
            result = await db_session.scalar(stmt.returning(Achievement))
            return result
