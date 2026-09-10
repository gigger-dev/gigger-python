import datetime
from abc import ABC, abstractmethod
from typing import List, Tuple
from uuid import UUID

import sqlalchemy as sa
from core.config import settings
from core.global_import import AsyncSession
from core.response import PaginatedResponse, SimpleResponse
from fastapi import HTTPException
from features.accounts.models import Account
from features.events.models import Event, event_like_many_to_many
from features.gig_list.models import GigList, gig_list_like_many_to_many
from features.post.models import Post, post_like_many_to_many
from features.profile import models, schemas
from features.settings.models import Notification
from features.settings.schemas import (
    NotificationBodySchema,
    NotificationIn,
    NotificationType,
)
from features.sup.models import Sup, sup_like_many_to_many
from sqlalchemy.orm import aliased


class ProfileRepo(ABC):
    @abstractmethod
    async def list_interests(self, query: str) -> list[schemas.InterestOut]:
        pass

    @abstractmethod
    async def list_services(self, query: str) -> list[schemas.MyServicesOut]:
        pass

    @abstractmethod
    async def list_skills(self, query: str) -> list[schemas.SkillOut]:
        pass

    @abstractmethod
    async def create_profile(self, body: schemas.ProfileIn) -> schemas.ProfileOut:
        pass

    @abstractmethod
    async def get_profile(self, account_uuid: UUID) -> schemas.ProfileOut:
        pass

    @abstractmethod
    async def update_profile(
        self, profile_uuid: UUID, body: schemas.ProfileUpdate
    ) -> schemas.ProfileOut:
        pass

    @abstractmethod
    async def list_profiles_for_given_profile(
        self, profile_uuid: UUID, limit: int = 100, offset: int = 0
    ) -> PaginatedResponse[schemas.ProfileOut]:
        pass

    @abstractmethod
    async def get_others_profile(self, profile_uuid: UUID) -> schemas.ProfileOut:
        pass

    @abstractmethod
    async def get_metadata(
        self, profile_uuid: UUID, self_uuid: UUID
    ) -> schemas.ProfileMetaDataOut:
        pass

    @abstractmethod
    async def toggle_private_mode(
        self, profile_uuid: UUID, is_private: bool
    ) -> schemas.ProfileOut:
        pass

    @abstractmethod
    async def view_profile(
        self,
        viewer_uuid: UUID,
        profile_uuid: UUID,
    ) -> schemas.ProfileMetaDataOut:
        pass

    @abstractmethod
    async def search_profile(
        self,
        searcher_uuid: UUID,
        username: str | None,
        role: str | None,
        genre: str | None,
        instrument: str | None,
        availability: schemas.AvailabilitySearchParam | None,
        limit: int = 50,
        offset: int = 0,
        pro_user_only: bool = False,
    ) -> PaginatedResponse[schemas.ProfileOut]:
        pass


# TODO
# need to implement private profile
class ProfileRepoImpl(ProfileRepo):
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def list_interests(self, query: str) -> list[schemas.InterestOut]:
        if query:
            stmt = (
                sa.select(models.Interest)
                .where(models.Interest.name.ilike(f"%{query}%"))
                .order_by(
                    models.Interest.name.ilike(
                        f"{query}%"
                    ).desc(),  # Starts-with match first
                    models.Interest.name,  # Alphabetical order
                )
            )
        else:
            stmt: sa.Select[Tuple[models.Interest]] = sa.select(
                models.Interest
            ).order_by(models.Interest.name)
        result: sa.ScalarResult[models.Interest] = await self.db_session.scalars(
            stmt.limit(50)
        )
        return [result.to_pydantic() for result in result.all()]

    async def list_services(self, query: str) -> list[schemas.MyServicesOut]:
        if query:
            stmt = (
                sa.select(models.MyServices)
                .where(models.MyServices.name.ilike(f"%{query}%"))
                .order_by(
                    models.MyServices.name.ilike(
                        f"{query}%"
                    ).desc(),  # Starts-with match first
                    models.MyServices.name,  # Alphabetical order
                )
            )
        else:
            stmt: sa.Select[Tuple[models.MyServices]] = sa.select(
                models.MyServices
            ).order_by(models.MyServices.name)
        result: sa.ScalarResult[models.MyServices] = await self.db_session.scalars(
            stmt.limit(50)
        )
        return [result.to_pydantic() for result in result.all()]

    async def list_skills(self, query: str) -> list[schemas.SkillOut]:
        if query:
            stmt = (
                sa.select(models.Skill)
                .where(models.Skill.name.ilike(f"%{query}%"))
                .order_by(
                    models.Skill.name.ilike(
                        f"{query}%"
                    ).desc(),  # Starts-with match first
                    models.Skill.name,  # Alphabetical order
                )
            )
        else:
            stmt: sa.Select[Tuple[models.Skill]] = sa.select(models.Skill).order_by(
                models.Skill.name
            )
        result: sa.ScalarResult[models.Skill] = await self.db_session.scalars(
            stmt.limit(50)
        )
        return [result.to_pydantic() for result in result.all()]

    async def create_profile(self, body: schemas.ProfileIn) -> schemas.ProfileOut:
        result = await models.Profile.create_profile(
            db_session=self.db_session, profile_in=body
        )
        if result:
            return result.to_pydantic()

        raise HTTPException(status_code=500, detail="Failed to create profile!")

    async def get_profile(self, account_uuid: UUID) -> schemas.ProfileOut:
        result = await models.Profile.get(
            db_session=self.db_session,
            account_uuid=account_uuid,
            selectinload=models.Profile.location,
        )
        if result:
            return result.to_pydantic()
        raise HTTPException(status_code=404, detail="Profile not found!")

    async def update_profile(
        self, profile_uuid: UUID, body: schemas.ProfileUpdate
    ) -> schemas.ProfileOut:
        profile = await models.Profile.get(
            db_session=self.db_session,
            uuid=profile_uuid,
            selectinload=models.Profile.location,
        )
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found!")

        try:
            result = await models.Profile.update_profile(
                db_session=self.db_session,
                profile_update=body,
            )
            if result:
                return result.to_pydantic()
            raise HTTPException(status_code=500, detail="Failed to update profile!")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def list_profiles_for_given_profile(
        self, profile_uuid: UUID, limit: int = 100, offset: int = 0
    ) -> PaginatedResponse[schemas.ProfileOut]:
        profile = await models.Profile.get(
            db_session=self.db_session,
            uuid=profile_uuid,
        )
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found!")

        account_alias = aliased(Account, name="account_alias")
        base_stmt = (
            sa.select(models.Profile)
            .outerjoin(account_alias, models.Profile.account_uuid == account_alias.uuid)
            # .outerjoin(account_alias, models.Profile.account_uuid == Account.uuid) eg blocked_user
            .where(
                models.Profile.uuid != profile_uuid,
                account_alias.is_active.is_(True),
                account_alias.is_banned.is_(False),
            )
        ).order_by(models.Profile.created_at.desc())
        count_stmt = sa.select(sa.func.count()).select_from(base_stmt.subquery())

        items_stmt = base_stmt.order_by(sa.func.random()).offset(offset).limit(limit)

        total = await self.db_session.scalar(count_stmt)

        items = await self.db_session.scalars(items_stmt)

        return PaginatedResponse(
            limit=limit,
            offset=offset,
            total=total or 0,
            items=[item.to_pydantic() for item in items],
        )

    async def get_others_profile(self, profile_uuid: UUID) -> schemas.ProfileOut:
        profile = await models.Profile.get(
            db_session=self.db_session,
            uuid=profile_uuid,
        )
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found!")

        return profile.to_pydantic()

    async def _get_follower_count(self, db_session: AsyncSession, profile_uuid: UUID):
        stmt = (
            sa.select(sa.func.count())
            .select_from(models.profile_followers_many_to_many)
            .where(
                models.profile_followers_many_to_many.c.profile_uuid == profile_uuid,
            )
        )
        result = await db_session.execute(stmt)
        return result.scalar()

    async def _get_following_count(self, db_session: AsyncSession, profile_uuid: UUID):
        stmt = (
            sa.select(sa.func.count())
            .select_from(models.profile_followers_many_to_many)
            .where(
                models.profile_followers_many_to_many.c.follower_uuid == profile_uuid,
            )
        )
        result = await db_session.execute(stmt)
        return result.scalar()

    async def _get_like_count(self, db_session: AsyncSession, profile_uuid: UUID):
        post_count = (
            sa.select(sa.func.count())
            .select_from(
                post_like_many_to_many.join(
                    Post,
                    Post.uuid == post_like_many_to_many.c.post_uuid,
                )
            )
            .where(Post.profile_uuid == profile_uuid)
        )
        sup_count = (
            sa.select(sa.func.count())
            .select_from(
                sup_like_many_to_many.join(
                    Sup, Sup.uuid == sup_like_many_to_many.c.sup_uuid
                )
            )
            .where(Sup.profile_uuid == profile_uuid)
        )
        gig_count = (
            sa.select(sa.func.count())
            .select_from(
                gig_list_like_many_to_many.join(
                    GigList, GigList.uuid == gig_list_like_many_to_many.c.gig_list_uuid
                )
            )
            .where(GigList.profile_uuid == profile_uuid)
        )
        event_count = (
            sa.select(sa.func.count())
            .select_from(
                event_like_many_to_many.join(
                    Event, Event.uuid == event_like_many_to_many.c.event_uuid
                )
            )
            .where(Event.profile_uuid == profile_uuid)
        )

        total_stmt = sa.select(
            post_count.scalar_subquery()
            + sup_count.scalar_subquery()
            + gig_count.scalar_subquery()
            + event_count.scalar_subquery()
        )

        result = await db_session.execute(total_stmt)
        return result.scalar_one()

    async def _get_view_count(self, db_session: AsyncSession, profile_uuid: UUID):
        stmt = (
            sa.select(sa.func.count())
            .select_from(models.profile_viewer_many_to_many)
            .where(
                models.profile_viewer_many_to_many.c.profile_uuid == profile_uuid,
            )
        )
        result = await db_session.execute(stmt)
        return result.scalar()

    async def _check_if_already_liked_profile(
        self, profile_uuid: UUID, liker_uuid: UUID
    ):
        is_already_liked_stmt = (
            sa.select(sa.func.count())
            .select_from(models.profile_like_many_to_many)
            .where(
                models.profile_like_many_to_many.c.profile_uuid == profile_uuid,
                models.profile_like_many_to_many.c.liker_uuid == liker_uuid,
            )
        )
        count = await self.db_session.scalar(is_already_liked_stmt)
        return count is not None and count > 0

    async def get_metadata(
        self,
        profile_uuid: UUID,
        self_uuid: UUID,
    ) -> schemas.ProfileMetaDataOut:
        profile = await models.Profile.get(
            db_session=self.db_session,
            uuid=profile_uuid,
        )
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found!")
        follower_count = await self._get_follower_count(
            db_session=self.db_session, profile_uuid=profile_uuid
        )
        following_count = await self._get_following_count(
            db_session=self.db_session, profile_uuid=profile_uuid
        )
        like_count = await self._get_like_count(
            db_session=self.db_session, profile_uuid=profile_uuid
        )
        view_count = await self._get_view_count(
            db_session=self.db_session, profile_uuid=profile_uuid
        )
        is_self = profile.uuid == self_uuid
        relationship_meta_data = None

        if not is_self:
            is_already_following_stmt = (
                sa.select(sa.func.count())
                .select_from(models.profile_followers_many_to_many)
                .where(
                    models.profile_followers_many_to_many.c.profile_uuid
                    == profile_uuid,
                    models.profile_followers_many_to_many.c.follower_uuid == self_uuid,
                )
            )
            is_already_following = await self.db_session.scalar(
                is_already_following_stmt
            )
            is_already_requested_to_follow = None
            if profile.is_private_profile:
                is_already_requested_stmt = (
                    sa.select(sa.func.count())
                    .select_from(models.follower_request_many_to_many)
                    .where(
                        models.follower_request_many_to_many.c.profile_uuid
                        == profile_uuid,
                        models.follower_request_many_to_many.c.follower_uuid
                        == self_uuid,
                    )
                )
                is_already_requested_to_follow = await self.db_session.scalar(
                    is_already_requested_stmt
                )

            relationship_meta_data = schemas.RelationshipMetaDataOut(
                is_already_following=bool(is_already_following),
                is_already_requested_to_follow=bool(is_already_requested_to_follow),
            )

        return schemas.ProfileMetaDataOut(
            followers_count=follower_count or 0,
            following_count=following_count or 0,
            like_count=like_count or 0,
            view_count=view_count or 0,
            is_self=is_self,
            relationship_meta_data=relationship_meta_data,
        )

    async def toggle_private_mode(
        self, profile_uuid: UUID, is_private: bool
    ) -> schemas.ProfileOut:
        profile = await models.Profile.get(
            db_session=self.db_session,
            uuid=profile_uuid,
        )
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found!")
        if profile.is_private_profile != is_private:
            await profile.update(
                is_private_profile=is_private, db_session=self.db_session
            )
        return profile.to_pydantic()

    # async def like_unlike_profile(
    #     self, liker_uuid: UUID, profile_uuid: UUID
    # ) -> schemas.ProfileMetaDataOut:
    #     _check_if_already_liked_profile = await self._check_if_already_liked_profile(
    #         profile_uuid=profile_uuid, liker_uuid=liker_uuid
    #     )
    #     if not _check_if_already_liked_profile:
    #         stmt = sa.insert(models.profile_like_many_to_many).values(
    #             profile_uuid=profile_uuid, liker_uuid=liker_uuid
    #         )
    #         await self.db_session.execute(stmt)
    #         await self.db_session.commit()
    #         _check_if_already_liked_profile = True
    #     else:
    #         stmt = sa.delete(models.profile_like_many_to_many).where(
    #             models.profile_like_many_to_many.c.profile_uuid == profile_uuid,
    #             models.profile_like_many_to_many.c.liker_uuid == liker_uuid,
    #         )
    #         await self.db_session.execute(stmt)
    #         await self.db_session.commit()
    #         _check_if_already_liked_profile = False

    #     return await self.get_metadata(
    #         profile_uuid=profile_uuid,
    #         self_uuid=liker_uuid,
    #     )

    async def view_profile(
        self, viewer_uuid: UUID, profile_uuid: UUID
    ) -> schemas.ProfileMetaDataOut:
        is_already_viewed_stmt = (
            sa.select(sa.func.count())
            .select_from(models.profile_viewer_many_to_many)
            .where(
                models.profile_viewer_many_to_many.c.profile_uuid == profile_uuid,
                models.profile_viewer_many_to_many.c.viewer_uuid == viewer_uuid,
            )
        )
        existing_view = await self.db_session.scalar(is_already_viewed_stmt)

        if not existing_view:
            stmt = sa.insert(models.profile_viewer_many_to_many).values(
                profile_uuid=profile_uuid, viewer_uuid=viewer_uuid
            )
            await self.db_session.execute(stmt)
            await self.db_session.commit()
            viewer_profile = await models.Profile.get(
                db_session=self.db_session, uuid=viewer_uuid
            )
            if not viewer_profile:
                raise HTTPException(status_code=404, detail="Profile not found!")
            if profile_uuid != viewer_uuid:
                notification_body = NotificationBodySchema(
                    profile_uuid=str(viewer_uuid),
                    notification_type=NotificationType.NEW_VIEW.value,
                    profile_image=str(viewer_profile.avatar_media),
                    profile_name=str(viewer_profile.account.username),
                    uuid=str(viewer_profile.uuid),
                )
                notification_in = NotificationIn(
                    title="New View",
                    body=f"{viewer_profile.account.username} viewed your Profile!",
                    notification_type=NotificationType.NEW_VIEW.value,
                    profile_uuid=profile_uuid,
                    data=notification_body.model_dump(),
                )
                notification_out = await Notification.create(
                    db_session=self.db_session, **notification_in.model_dump()
                )
                if notification_out and not settings.debug:
                    await notification_out.send_multicast_notification(
                        profile_uuid_to_send_notification=profile_uuid,
                        db_session=self.db_session,
                    )
            existing_view = True
        return await self.get_metadata(profile_uuid, viewer_uuid)

    async def search_profile(
        self,
        searcher_uuid: UUID,
        username: str | None,
        role: str | None,
        genre: str | None,
        instrument: str | None,
        availability: schemas.AvailabilitySearchParam | None,
        limit: int = 50,
        offset: int = 0,
        pro_user_only: bool = False,
        follower_only: bool = False,
    ) -> PaginatedResponse[schemas.ProfileOut]:
        # username is not none
        stmt = sa.select(models.Profile).join(Account)

        if follower_only:
            stmt = stmt.join(models.profile_followers_many_to_many).where(
                models.profile_followers_many_to_many.c.profile_uuid == searcher_uuid
            )

        if username:
            stmt = stmt.where(Account.username.ilike(f"%{username}%"))
        # Filter by role

        if role:
            stmt = stmt.join(
                models.Profile.skills
            )  # Use ORM relationship instead of manual JOIN

            stmt = stmt.where(models.Skill.name.ilike(f"%{role}%"))

        # Filter by genre
        if genre:
            stmt = stmt.join(
                models.Profile.interests
            )  # Use ORM relationship for interests
            stmt = stmt.where(models.Interest.name.ilike(f"%{genre}%"))
        if instrument:
            stmt = stmt.outerjoin(
                models.Profile.skills
            )  # Join skills via ORM relationship
            stmt = stmt.outerjoin(
                models.Profile.achievements
            )  # Join achievements via ORM relationship

            stmt = stmt.where(
                sa.or_(
                    models.Skill.name.ilike(f"%{instrument}%"),
                    models.Profile.bio.ilike(f"%{instrument}%"),
                    models.Achievement.name.ilike(f"%{instrument}%"),
                    models.Achievement.category.ilike(f"%{instrument}%"),
                    models.Achievement.url.ilike(f"%{instrument}%"),
                )
            )

            # search in bo

        if availability:
            search_start_weekday = availability.start_date.isoweekday()
            search_end_weekday = availability.end_date.isoweekday()
            search_start_time = availability.start_date.time()
            search_end_time = availability.end_date.time()
            # Calculate the range of weekdays to search
            weekdays_to_search = [search_start_weekday, search_end_weekday]

            stmt = stmt.join(
                models.Profile.availability,
            ).where(
                sa.and_(
                    models.Availability.day.in_(weekdays_to_search),
                    models.Availability.start_time <= search_start_time,
                    models.Availability.end_time >= search_end_time,
                    # sa.or_(
                    #     # Case 1: Availability fully within the search time range
                    #     # Case 2: Availability overlaps the start of the search time range
                    #     # sa.and_(
                    #     #     models.Availability.start_time <= search_start_time,
                    #     #     models.Availability.end_time > search_start_time,
                    #     # ),
                    #     # # Case 3: Availability overlaps the end of the search time range
                    #     # sa.and_(
                    #     #     models.Availability.start_time < search_end_time,
                    #     #     models.Availability.end_time >= search_end_time,
                    #     # ),
                    #     # # Case 4: Availability encompasses the entire search time range
                    #     # sa.and_(
                    #     #     models.Availability.start_time <= search_start_time,
                    #     #     models.Availability.end_time >= search_end_time,
                    #     # ),
                    # ),
                )
            )
        if self.db_session.bind.dialect.name == "postgresql":
            stmt = stmt.order_by(models.Profile.uuid)
            stmt = stmt.distinct(models.Profile.uuid)

        stmt = stmt.order_by(
            Account.username.ilike(f"{username}%").desc(),  # Starts-with match first
            Account.username,  # Alphabetical order
        )
        total_count = sa.select(sa.func.count()).select_from(stmt.subquery())
        total = await self.db_session.scalar(total_count)
        result = await self.db_session.scalars(
            stmt.limit(limit).offset(offset),
        )
        return PaginatedResponse(
            limit=limit,
            offset=offset,
            total=total or 0,
            items=[item.to_pydantic() for item in result],
        )


class NewFollowerRepo(ABC):
    @abstractmethod
    async def list_my_follower(
        self, profile_uuid: UUID, limit: int, offset: int
    ) -> PaginatedResponse[schemas.ProfileFewerDetailsOut]:
        pass

    @abstractmethod
    async def list_my_following(
        self, profile_uuid: UUID, limit: int, offset: int
    ) -> PaginatedResponse[schemas.ProfileFewerDetailsOut]:
        pass

    @abstractmethod
    async def search_my_follower(
        self,
        profile_uuid: UUID,
        username: str,
    ) -> List[schemas.ProfileFewerDetailsOut]:
        pass

    @abstractmethod
    async def follow_another_profile(
        self, profile_to_follow: UUID, follower_uuid: UUID
    ) -> SimpleResponse:
        pass

    @abstractmethod
    async def unfollow_another_profile(
        self, profile_to_unfollow: UUID, follower_uuid: UUID
    ) -> SimpleResponse:
        pass

    @abstractmethod
    async def remove_my_follower(
        self, profile_to_remove: UUID, self_profile: UUID
    ) -> SimpleResponse:
        pass

    @abstractmethod
    async def request_to_follow_for_private_profile(
        self, profile_to_request_to_follow: UUID, follower_requester_uuid: UUID
    ) -> SimpleResponse:
        pass

    @abstractmethod
    async def accept_or_reject_request_to_follow_for_private_profile(
        self,
        profile_to_accept_or_reject: UUID,
        follower_accepter_or_rejecter_uuid: UUID,
        is_accepted: bool,
    ) -> SimpleResponse:
        pass

    @abstractmethod
    async def cancel_request_to_follow_for_private_profile(
        self,
        canceler: UUID,
        profile_to_cancel_follow_request: UUID,
    ) -> SimpleResponse:
        pass


class NewFollowerRepoImpl(NewFollowerRepo):
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def _check_if_already_following(
        self, profile_to_follow: UUID, follower_uuid: UUID
    ) -> bool:
        is_already_following_stmt = (
            sa.select(sa.func.count())
            .select_from(models.profile_followers_many_to_many)
            .where(
                models.profile_followers_many_to_many.c.profile_uuid
                == profile_to_follow,
                models.profile_followers_many_to_many.c.follower_uuid == follower_uuid,
            )
        )
        is_already_following = await self.db_session.scalar(is_already_following_stmt)
        return is_already_following is not None and is_already_following > 0

    async def _check_is_my_follower_or_not(
        self, profile_to_check: UUID, self_profile: UUID
    ) -> bool:
        is_my_follower_stmt = (
            sa.select(sa.func.count())
            .select_from(models.profile_followers_many_to_many)
            .where(
                models.profile_followers_many_to_many.c.profile_uuid == self_profile,
                models.profile_followers_many_to_many.c.follower_uuid
                == profile_to_check,
            )
        )
        is_my_follower = await self.db_session.scalar(is_my_follower_stmt)
        return is_my_follower is not None and is_my_follower > 0

    async def _check_if_already_requested_to_follow(
        self, profile_to_request_to_follow: UUID, follower_requester_uuid: UUID
    ) -> bool:
        is_already_requested_stmt = (
            sa.select(sa.func.count())
            .select_from(models.follower_request_many_to_many)
            .where(
                models.follower_request_many_to_many.c.profile_uuid
                == profile_to_request_to_follow,
                models.follower_request_many_to_many.c.follower_uuid
                == follower_requester_uuid,
            )
        )
        is_already_requested = await self.db_session.scalar(is_already_requested_stmt)
        return is_already_requested is not None and is_already_requested > 0

    async def follow_another_profile(
        self, profile_to_follow: UUID, follower_uuid: UUID
    ) -> SimpleResponse:
        # check if already following or not
        is_already_following = await self._check_if_already_following(
            profile_to_follow=profile_to_follow, follower_uuid=follower_uuid
        )
        if is_already_following:
            raise HTTPException(
                status_code=400, detail="Already following this profile!"
            )
        insert_stmt = sa.insert(models.profile_followers_many_to_many).values(
            profile_uuid=profile_to_follow,
            follower_uuid=follower_uuid,
            created_at=datetime.datetime.now(datetime.UTC),
        )
        await self.db_session.execute(insert_stmt)
        await self.db_session.commit()
        # save to notification table
        follower_profile = await models.Profile.get(
            db_session=self.db_session, uuid=follower_uuid
        )
        if not follower_profile:
            raise HTTPException(status_code=404, detail="Profile to follow not found!")
        if profile_to_follow != follower_uuid:
            notification_body = NotificationBodySchema(
                profile_uuid=str(follower_uuid),
                notification_type=NotificationType.NEW_FOLLOWER.value,
                profile_image=str(follower_profile.avatar_media),
                profile_name=str(follower_profile.account.username),
                uuid=str(follower_profile.uuid),
            )
            notification_in = NotificationIn(
                title="New Follower",
                body=f"{follower_profile.account.username} followed you!",
                notification_type=NotificationType.NEW_FOLLOWER.value,
                profile_uuid=profile_to_follow,
                data=notification_body.model_dump(),
            )
            notification_out = await Notification.create(
                db_session=self.db_session, **notification_in.model_dump()
            )
            if notification_out and not settings.debug:
                await notification_out.send_multicast_notification(
                    profile_uuid_to_send_notification=profile_to_follow,
                    db_session=self.db_session,
                )
        return SimpleResponse(message="Followed successfully!", status_code=200)

    async def unfollow_another_profile(
        self, profile_to_unfollow: UUID, follower_uuid: UUID
    ) -> SimpleResponse:
        # check if already following or not
        is_already_following = await self._check_if_already_following(
            profile_to_follow=profile_to_unfollow, follower_uuid=follower_uuid
        )
        if not is_already_following:
            raise HTTPException(status_code=400, detail="Not following this profile!")
        delete_stmt = sa.delete(models.profile_followers_many_to_many).where(
            models.profile_followers_many_to_many.c.profile_uuid == profile_to_unfollow,
            models.profile_followers_many_to_many.c.follower_uuid == follower_uuid,
        )
        await self.db_session.execute(delete_stmt)
        await self.db_session.commit()
        return SimpleResponse(message="Unfollowed successfully!", status_code=200)

    async def remove_my_follower(
        self, profile_to_remove: UUID, self_profile: UUID
    ) -> SimpleResponse:
        """
        Remove profile from my follower.

        Args:
            profile_to_remove (UUID): _description_
            follower_uuid (UUID): _description_

        Raises:
            HTTPException: _description_

        Returns:
            SimpleResponse:
        """
        is_my_follower = await self._check_is_my_follower_or_not(
            profile_to_check=profile_to_remove, self_profile=self_profile
        )
        if not is_my_follower:
            raise HTTPException(
                status_code=400, detail="This profile is not your follower!"
            )
        delete_stmt = sa.delete(models.profile_followers_many_to_many).where(
            models.profile_followers_many_to_many.c.profile_uuid == self_profile,
            models.profile_followers_many_to_many.c.follower_uuid == profile_to_remove,
        )
        await self.db_session.execute(delete_stmt)
        await self.db_session.commit()
        return SimpleResponse(message="Follower removed successfully!", status_code=200)

    async def request_to_follow_for_private_profile(
        self, profile_to_request_to_follow: UUID, follower_requester_uuid: UUID
    ) -> SimpleResponse:
        check_if_already_requested = await self._check_if_already_requested_to_follow(
            profile_to_request_to_follow=profile_to_request_to_follow,
            follower_requester_uuid=follower_requester_uuid,
        )
        if check_if_already_requested:
            raise HTTPException(
                status_code=400, detail="Already requested to follow this profile!"
            )
        insert_stmt = sa.insert(models.follower_request_many_to_many).values(
            profile_uuid=profile_to_request_to_follow,
            follower_uuid=follower_requester_uuid,
        )
        await self.db_session.execute(insert_stmt)
        await self.db_session.commit()
        if not settings.debug:
            requester_profile = await models.Profile.get(
                db_session=self.db_session, uuid=follower_requester_uuid
            )
            if not requester_profile:
                raise HTTPException(
                    status_code=404, detail="Requester profile not found!"
                )
            if requester_profile != profile_to_request_to_follow:
                notification_body = NotificationBodySchema(
                    profile_uuid=str(profile_to_request_to_follow),
                    notification_type=NotificationType.NEW_FOLLOW_REQUEST.value,
                    profile_image=str(requester_profile.avatar_media),
                    profile_name=str(requester_profile.account.username),
                    uuid=str(requester_profile.uuid),
                )
                notification_in = NotificationIn(
                    title="New Follow Request",
                    body=f"{requester_profile.account.username} request to follow you!",
                    notification_type=NotificationType.NEW_FOLLOW_REQUEST.value,
                    profile_uuid=profile_to_request_to_follow,
                    data=notification_body.model_dump(),
                )
                notification_out = await Notification.create(
                    db_session=self.db_session, **notification_in.model_dump()
                )
                if notification_out and not settings.debug:
                    await notification_out.send_multicast_notification(
                        profile_uuid_to_send_notification=profile_to_request_to_follow,
                        db_session=self.db_session,
                    )

        return SimpleResponse(message="Request sent successfully!", status_code=200)

    async def accept_or_reject_request_to_follow_for_private_profile(
        self,
        profile_to_accept_or_reject: UUID,
        follower_accepter_or_rejecter_uuid: UUID,
        is_accepted: bool,
    ) -> SimpleResponse:
        # if is_accepted is True, then add to profile_followers_many_to_many table
        is_already_requested = await self._check_if_already_requested_to_follow(
            profile_to_request_to_follow=follower_accepter_or_rejecter_uuid,
            follower_requester_uuid=profile_to_accept_or_reject,
        )
        if not is_already_requested:
            raise HTTPException(
                status_code=400, detail="No request found to accept or reject!"
            )
        if is_accepted:
            insert_stmt = sa.insert(models.profile_followers_many_to_many).values(
                profile_uuid=follower_accepter_or_rejecter_uuid,
                follower_uuid=profile_to_accept_or_reject,
                created_at=datetime.datetime.now(datetime.UTC),
            )  # follower အနေနဲ့ပဲလက်ခံမယ်
            await self.db_session.execute(insert_stmt)
            await self.db_session.commit()
            # save to notification table
            accepter = await models.Profile.get(
                db_session=self.db_session, uuid=follower_accepter_or_rejecter_uuid
            )
            if not accepter:
                raise HTTPException(
                    status_code=404, detail="Accepter profile not found!"
                )
            if profile_to_accept_or_reject != follower_accepter_or_rejecter_uuid:
                notification_body = NotificationBodySchema(
                    profile_uuid=str(follower_accepter_or_rejecter_uuid),
                    notification_type=NotificationType.REQUEST_ACCEPTED.value,
                    profile_image=str(accepter.avatar_media),
                    profile_name=str(accepter.account.username),
                    uuid=str(accepter.uuid),
                )
                notification_in = NotificationIn(
                    title="Accepted Follow Request",
                    body=f"{accepter.account.username} accepted your follow request!",
                    notification_type=NotificationType.REQUEST_ACCEPTED.value,
                    profile_uuid=profile_to_accept_or_reject,
                    data=notification_body.model_dump(),
                )
                notification_out = await Notification.create(
                    db_session=self.db_session, **notification_in.model_dump()
                )
                if notification_out and not settings.debug:
                    await notification_out.send_multicast_notification(
                        profile_uuid_to_send_notification=profile_to_accept_or_reject,
                        db_session=self.db_session,
                    )
        # delete request from follower_request_many_to_many table
        delete_stmt = sa.delete(models.follower_request_many_to_many).where(
            models.follower_request_many_to_many.c.profile_uuid
            == follower_accepter_or_rejecter_uuid,
            models.follower_request_many_to_many.c.follower_uuid
            == profile_to_accept_or_reject,
        )
        await self.db_session.execute(delete_stmt)
        await self.db_session.commit()
        return SimpleResponse(message="Request accepted successfully!", status_code=200)

    async def list_my_follower(
        self, profile_uuid: UUID, limit: int, offset: int
    ) -> PaginatedResponse[schemas.ProfileFewerDetailsOut]:
        #     followers_table = models.profile_followers_many_to_many.name

        #     profiles_table = models.Profile.__tablename__

        #     count_query = sa.text("""
        #       SELECT COUNT(*)
        # FROM gigger_profile_followers gpf
        # LEFT JOIN gigger_profiles p
        #   ON p.uuid = gpf.follower_uuid
        # WHERE gpf.profile_uuid = :profile_uuid;
        # """)

        #     total_count = await self.db_session.scalar(
        #         count_query, {"profile_uuid": str(profile_uuid)}
        #     )
        #     query = sa.text(f"""
        #     SELECT p.*
        #         --    CASE
        #         --        WHEN gpf_reverse.profile_uuid IS NOT NULL THEN true
        #         --        ELSE false
        #         --    END AS is_followed_back
        #     FROM {followers_table} gpf
        #     JOIN {profiles_table} p
        #         ON p.uuid = gpf.follower_uuid
        #     -- LEFT JOIN {followers_table} gpf_reverse
        #     --     ON gpf_reverse.profile_uuid = gpf.follower_uuid
        #     --     AND gpf_reverse.follower_uuid = gpf.profile_uuid
        #     WHERE gpf.profile_uuid = :profile_uuid
        #     ORDER BY gpf.profile_uuid ASC, gpf.follower_uuid ASC
        #     LIMIT :limit OFFSET :offset;
        # """)
        #     result = await self.db_session.scalars(
        #         query,
        #         {
        #             "profile_uuid": str(profile_uuid),
        #             "limit": int(limit),
        #             "offset": int(offset),
        #         },
        #     )
        #     rows = result.all()

        #     items = [schemas.ProfileFewerDetailsOut(**row) for row in rows]
        #     return PaginatedResponse(
        #         total=int(total_count or 0),
        #         limit=limit,
        #         offset=offset,
        #         items=items,
        #     )
        gpf = models.profile_followers_many_to_many
        gpf_reverse = aliased(models.profile_followers_many_to_many)
        fr = models.follower_request_many_to_many

        fr_alias = aliased(fr)

        followers_query = (
            sa.select(
                models.Profile,
                sa.case(
                    (gpf_reverse.c.profile_uuid.isnot(None), sa.true()),
                    else_=sa.false(),
                ).label("is_followed_back"),
                sa.case(
                    (fr_alias.c.profile_uuid.isnot(None), sa.true()),
                    else_=sa.false(),
                ).label("is_follow_request_already_sent"),
            )
            .join(gpf, gpf.c.follower_uuid == models.Profile.uuid)
            .outerjoin(
                gpf_reverse,
                sa.and_(
                    gpf_reverse.c.profile_uuid == gpf.c.follower_uuid,
                    gpf_reverse.c.follower_uuid == gpf.c.profile_uuid,
                ),
            )
            .outerjoin(
                fr_alias,
                sa.and_(
                    fr_alias.c.profile_uuid == gpf.c.follower_uuid,
                    fr_alias.c.follower_uuid == gpf.c.profile_uuid,
                ),
            )
            .filter(gpf.c.profile_uuid == profile_uuid)
            .order_by(gpf.c.profile_uuid.asc(), gpf.c.follower_uuid.desc())
        )
        # Count query: use a subquery based on the followers_query.
        total_count = await self.db_session.scalar(
            sa.select(sa.func.count()).select_from(followers_query.subquery()),
        )
        result = await self.db_session.execute(
            followers_query.limit(limit).offset(offset),
            {"profile_uuid": str(profile_uuid)},
        )
        rows = result.all()
        items: List[schemas.ProfileFewerDetailsOut] = []
        for profile, is_follow_back, is_follow_request_already_sent in rows:
            profile_data = profile.to_pydantic_fewer_details(
                is_followed_back=is_follow_back,
                is_follow_request_already_sent=is_follow_request_already_sent,
            )
            items.append(profile_data)
        return PaginatedResponse(
            total=int(total_count or 0),
            limit=limit,
            offset=offset,
            items=items,
        )

    async def list_my_following(
        self, profile_uuid: UUID, limit: int, offset: int
    ) -> PaginatedResponse[schemas.ProfileFewerDetailsOut]:
        following = (
            sa.select(
                models.Profile,
            )
            .join(
                models.profile_followers_many_to_many,
                models.profile_followers_many_to_many.c.profile_uuid
                == models.Profile.uuid,
            )  # join the following table to profile table
            .filter(
                models.profile_followers_many_to_many.c.follower_uuid == profile_uuid,
            )
        )
        total_count = await self.db_session.scalar(
            sa.select(sa.func.count()).select_from(following.subquery())
        )
        items = await self.db_session.scalars(following.limit(limit).offset(offset))
        return PaginatedResponse(
            total=int(total_count or 0),
            limit=limit,
            offset=offset,
            items=[result.to_pydantic_fewer_details() for result in items.all()],
        )

    async def cancel_request_to_follow_for_private_profile(
        self, canceler: UUID, profile_to_cancel_follow_request: UUID
    ) -> SimpleResponse:
        has_already_request = await self._check_if_already_requested_to_follow(
            profile_to_request_to_follow=profile_to_cancel_follow_request,
            follower_requester_uuid=canceler,
        )
        if not has_already_request:
            raise HTTPException(
                status_code=400,
                detail="You haven't requested yet!",
            )
        delete_stmt = sa.delete(
            models.follower_request_many_to_many,
        ).where(
            models.follower_request_many_to_many.c.profile_uuid
            == profile_to_cancel_follow_request,
            models.follower_request_many_to_many.c.follower_uuid == canceler,
        )
        _ = await self.db_session.execute(delete_stmt)
        await self.db_session.commit()
        return SimpleResponse(
            status_code=200,
            message="Request cancelled successfully!",
        )

    async def search_my_follower(
        self, profile_uuid: UUID, username: str
    ) -> List[schemas.ProfileFewerDetailsOut]:
        stmt = (
            sa.select(
                models.Profile,
            )
            .join(Account)
            .join(
                models.profile_followers_many_to_many,
                models.profile_followers_many_to_many.c.follower_uuid
                == models.Profile.uuid,
            )
            .filter(
                models.profile_followers_many_to_many.c.profile_uuid == profile_uuid,
                Account.username.ilike(f"%{username}%"),
            )
        )
        result = await self.db_session.scalars(stmt.limit(10))
        return [result.to_pydantic_fewer_details() for result in result.all()]
