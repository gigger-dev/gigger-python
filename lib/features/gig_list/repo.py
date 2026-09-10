from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

import sqlalchemy as sa
from core.config import settings
from core.fileupload import delete_file_from_s3
from core.global_import import AsyncSession
from core.response import PaginatedResponse, SimpleResponse
from fastapi import HTTPException
from features.gig_list import models
from features.gig_list.schemas import (
    GigListCreate,
    GigListMetadata,
    GigListOut,
    GigListUpdate,
)
from features.profile.models import Profile
from features.settings.models import Notification
from features.settings.schemas import (
    NotificationBodySchema,
    NotificationIn,
    NotificationType,
)


class GigListRepo(ABC):
    @abstractmethod
    async def create_gig_list(self, body: GigListCreate) -> GigListOut:
        pass

    @abstractmethod
    async def list_gig_list(self, profile_uuid: UUID) -> PaginatedResponse[GigListOut]:
        pass

    @abstractmethod
    async def list_recommended_gig_list_for_given_profile(
        self, profile_uuid: UUID, limit: int = 100, offset: int = 0
    ) -> PaginatedResponse[GigListOut]:
        pass

    @abstractmethod
    async def delete_gig_list(
        self, gig_list_uuid: UUID, profile_uuid: UUID
    ) -> SimpleResponse:
        pass

    @abstractmethod
    async def update_gig_list(self, body: GigListUpdate) -> GigListOut:
        pass

    @abstractmethod
    async def list_gig_list_by_profile(
        self, profile_uuid: UUID, viewer_profile_uuid: UUID
    ) -> list[GigListOut]:
        pass

    @abstractmethod
    async def give_star(
        self,
        logged_in_profile_uuid: UUID,
        star_giver: UUID,
        gig_list_uuid: UUID,
    ) -> GigListMetadata:
        pass

    @abstractmethod
    async def get_metadata(
        self,
        gig_list_uuid: UUID,
        logged_in_profile_uuid: UUID,
        viewer_uuid: UUID,
    ) -> GigListMetadata:
        pass

    @abstractmethod
    async def like_unlike_gig_list(
        self,
        logged_in_profile_uuid: UUID,
        liker_uuid: UUID,
        gig_list_uuid: UUID,
    ) -> GigListMetadata:
        pass

    @abstractmethod
    async def get_gig_list_by_uuid(
        self,
        gig_list_uuid: UUID,
    ) -> GigListOut:
        pass

    @abstractmethod
    async def search_giglist(
        self,
        searcher_uuid: UUID,
        title: str | None,
        price: float | None,
        place: str | None,
        is_looking_for: bool,
        is_performer: bool,
        limit: int = 50,
        offset: int = 0,
    ) -> PaginatedResponse[GigListOut]:
        pass

    @abstractmethod
    async def get_my_favorite_gig_list(
        self,
        logged_in_profile_uuid: UUID,
        profile_uuid: UUID,
    ) -> List[GigListOut]:
        pass


class GigListRepoImpl(GigListRepo):
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_gig_list(self, body: GigListCreate) -> GigListOut:
        try:
            gig_list = await models.GigList.create(
                db_session=self.db_session,
                **body.model_dump(
                    exclude_none=True,
                    exclude={"hashtags", "uuid"},
                ),
            )
            if not gig_list:
                raise HTTPException(
                    status_code=500, detail="Failed to create gig list!"
                )
            if body.hashtags:
                for hashtag in body.hashtags:
                    await gig_list.add_hashtags(
                        db_session=self.db_session, hash_tags=[hashtag]
                    )

            await self.db_session.flush()
            await self.db_session.commit()
            await self.db_session.refresh(gig_list)
            return gig_list.to_pydantic()

        except Exception:
            raise

    async def list_gig_list(self, profile_uuid: UUID) -> PaginatedResponse[GigListOut]:
        stmt = sa.select(models.GigList).where(
            models.GigList.profile_uuid == profile_uuid
        )
        result = await self.db_session.scalars(stmt)
        items = [result.to_pydantic() for result in result.all()]
        return PaginatedResponse(
            total=len(items),
            limit=50,
            offset=0,
            items=items,
        )

    async def list_recommended_gig_list_for_given_profile(
        self, profile_uuid: UUID, limit: int = 100, offset: int = 0
    ) -> PaginatedResponse[GigListOut]:
        # TODO: only return gig lists that user might be interested in
        stmt = sa.select(models.GigList).order_by(
            models.GigList.created_at.desc(),
        )

        total_stmt = sa.select(sa.func.count()).select_from(stmt.subquery())
        total = await self.db_session.scalar(total_stmt)
        result = await self.db_session.scalars(
            stmt.limit(limit).offset(offset).order_by(sa.func.random())
        )
        items = [result.to_pydantic() for result in result.all()]
        return PaginatedResponse(
            total=total or 0,
            limit=limit,
            offset=offset,
            items=items,
        )

    async def delete_gig_list(
        self, gig_list_uuid: UUID, profile_uuid: UUID
    ) -> SimpleResponse:
        gig_list = await models.GigList.get(
            db_session=self.db_session,
            uuid=gig_list_uuid,
            profile_uuid=profile_uuid,
        )
        if not gig_list:
            raise HTTPException(status_code=404, detail="Git list not found!")
        gig_list = gig_list.to_pydantic()  # type errorတက်လို့
        if not settings.debug:
            try:
                if gig_list.thumbnail_url:
                    await delete_file_from_s3(gig_list.thumbnail_url)
            except Exception as e:
                print(f"Error deleting thumbnail image {gig_list.thumbnail_url}: {e}")

            for k, v in gig_list.gig_list_media.items():
                try:
                    if v.media_url:
                        await delete_file_from_s3(v.media_url)
                except Exception as e:
                    print(f"Error deleting media file {v.media_url}: {e}")

        await models.GigList.delete(db_session=self.db_session, uuid=gig_list_uuid)
        return SimpleResponse(message="Gig list deleted successfully!", status_code=200)

    async def update_gig_list(self, body: GigListUpdate) -> GigListOut:
        gig_list = await models.GigList.get(db_session=self.db_session, uuid=body.uuid)
        if not gig_list:
            raise HTTPException(status_code=404, detail="Gig List not found!")
        gig_list_body = body.model_dump(
            exclude={"uuid", "profile_uuid", "hashtags", "tagged_profiles"},
            exclude_none=True,
        )

        await gig_list.update(
            db_session=self.db_session,
            **gig_list_body,
        )

        if body.hashtags:
            await gig_list.add_hashtags(
                db_session=self.db_session, hash_tags=body.hashtags
            )

        await self.db_session.flush()
        await self.db_session.commit()
        await self.db_session.refresh(gig_list)

        return gig_list.to_pydantic()

    async def list_gig_list_by_profile(
        self, profile_uuid: UUID, viewer_profile_uuid: UUID
    ) -> list[GigListOut]:
        select = sa.select(models.GigList).where(
            models.GigList.profile_uuid == profile_uuid
        )

        result = await self.db_session.execute(select)
        items = [result.to_pydantic() for result in result.scalars().unique().all()]
        return items

    async def _check_if_already_given_star(self, gig_list_uuid: UUID, star_giver: UUID):
        has_already_given_star_stmt = (
            sa.select(sa.func.count())
            .select_from(models.gig_list_stars_many_to_many)
            .where(
                models.gig_list_stars_many_to_many.c.gig_list_uuid == gig_list_uuid,
                models.gig_list_stars_many_to_many.c.viewer_uuid == star_giver,
            )
        )
        count = await self.db_session.scalar(has_already_given_star_stmt)
        return count is not None and count > 0

    async def _get_like_count(self, db_session: AsyncSession, gig_list_uuid: UUID):
        stmt = (
            sa.select(sa.func.count())
            .select_from(models.gig_list_like_many_to_many)
            .where(
                models.gig_list_like_many_to_many.c.gig_list_uuid == gig_list_uuid,
            )
        )
        return await self.db_session.scalar(stmt)

    async def _check_if_already_liked(self, gig_list_uuid: UUID, liker_uuid: UUID):
        is_already_liked_stmt = (
            sa.select(sa.func.count())
            .select_from(models.gig_list_like_many_to_many)
            .where(
                models.gig_list_like_many_to_many.c.gig_list_uuid == gig_list_uuid,
                models.gig_list_like_many_to_many.c.liker_uuid == liker_uuid,
            )
        )
        count = await self.db_session.scalar(is_already_liked_stmt)
        return count is not None and count > 0

    async def give_star(
        self, logged_in_profile_uuid: UUID, star_giver: UUID, gig_list_uuid: UUID
    ) -> GigListMetadata:
        _check_if_already_given_star = await self._check_if_already_given_star(
            gig_list_uuid=gig_list_uuid, star_giver=star_giver
        )
        if not _check_if_already_given_star:
            star_give_stmt = sa.insert(models.gig_list_stars_many_to_many).values(
                gig_list_uuid=gig_list_uuid, viewer_uuid=star_giver
            )
            await self.db_session.execute(star_give_stmt)
            await self.db_session.commit()
            _check_if_already_given_star = True
        else:
            delete_stmt = sa.delete(models.gig_list_stars_many_to_many).where(
                models.gig_list_stars_many_to_many.c.gig_list_uuid == gig_list_uuid,
                models.gig_list_stars_many_to_many.c.viewer_uuid == star_giver,
            )
            await self.db_session.execute(delete_stmt)
            await self.db_session.commit()
            _check_if_already_given_star = False

        return await self.get_metadata(
            gig_list_uuid=gig_list_uuid,
            logged_in_profile_uuid=logged_in_profile_uuid,
            viewer_uuid=star_giver,
            has_already_given_star=_check_if_already_given_star,
        )

    async def get_metadata(
        self,
        gig_list_uuid: UUID,
        logged_in_profile_uuid: UUID,
        viewer_uuid: UUID,
        has_already_given_star: bool | None = None,
        has_already_liked: bool | None = None,
    ) -> GigListMetadata:
        gig_list = await models.GigList.get(
            db_session=self.db_session, uuid=gig_list_uuid
        )
        _check_if_already_given_star = has_already_given_star
        if not _check_if_already_given_star:
            _check_if_already_given_star = await self._check_if_already_given_star(
                gig_list_uuid=gig_list_uuid, star_giver=viewer_uuid
            )
        total_star_stmt = (
            sa.select(sa.func.count())
            .select_from(models.gig_list_stars_many_to_many)
            .where(
                models.gig_list_stars_many_to_many.c.gig_list_uuid == gig_list_uuid,
            )
        )
        total_stars = await self.db_session.scalar(total_star_stmt)

        _check_if_already_liked = has_already_liked
        if not _check_if_already_liked:
            _check_if_already_liked = await self._check_if_already_liked(
                gig_list_uuid=gig_list_uuid, liker_uuid=viewer_uuid
            )
        total_like = await self._get_like_count(
            db_session=self.db_session, gig_list_uuid=gig_list_uuid
        )
        if not gig_list:
            raise HTTPException(
                status_code=400,
                detail="Gig_list not found!",
            )

        return GigListMetadata(
            has_already_given_star=_check_if_already_given_star or False,
            star_count=total_stars or 0,
            has_already_liked=_check_if_already_liked or False,
            like_count=total_like or 0,
        )

    async def like_unlike_gig_list(
        self, logged_in_profile_uuid: UUID, liker_uuid: UUID, gig_list_uuid: UUID
    ) -> GigListMetadata:
        _check_if_already_liked = await self._check_if_already_liked(
            gig_list_uuid=gig_list_uuid, liker_uuid=liker_uuid
        )
        if not _check_if_already_liked:
            stmt = sa.insert(models.gig_list_like_many_to_many).values(
                gig_list_uuid=gig_list_uuid, liker_uuid=liker_uuid
            )
            await self.db_session.execute(stmt)
            await self.db_session.commit()
            _check_if_already_liked = True

            gig_list = await models.GigList.get(
                db_session=self.db_session,
                uuid=gig_list_uuid,
            )
            if not gig_list:
                raise HTTPException(status_code=404, detail="Giglist not found!")
            liker_profile = await Profile.get(
                db_session=self.db_session, uuid=liker_uuid
            )
            if not liker_profile:
                raise HTTPException(status_code=404, detail="Profile not found!")
            if gig_list.profile_uuid != liker_profile.uuid:
                notification_body = NotificationBodySchema(
                    profile_uuid=str(liker_uuid),
                    notification_type=NotificationType.NEW_LIKE.value,
                    profile_image=str(liker_profile.avatar_media),
                    profile_name=str(liker_profile.account.username),
                    uuid=str(gig_list.uuid),
                )
                notification_in = NotificationIn(
                    title="New Like",
                    body=f"{liker_profile.account.username} liked your GigList!",
                    notification_type=NotificationType.NEW_LIKE.value,
                    profile_uuid=gig_list.profile_uuid,
                    data=notification_body.model_dump(),
                )
                notification_out = await Notification.create(
                    db_session=self.db_session, **notification_in.model_dump()
                )
                if notification_out and not settings.debug:
                    await notification_out.send_multicast_notification(
                        profile_uuid_to_send_notification=gig_list.profile_uuid,
                        db_session=self.db_session,
                    )
        else:
            stmt = sa.delete(models.gig_list_like_many_to_many).where(
                models.gig_list_like_many_to_many.c.gig_list_uuid == gig_list_uuid,
                models.gig_list_like_many_to_many.c.liker_uuid == liker_uuid,
            )
            await self.db_session.execute(stmt)
            await self.db_session.commit()
            _check_if_already_liked = False

        return await self.get_metadata(
            gig_list_uuid=gig_list_uuid,
            viewer_uuid=liker_uuid,
            logged_in_profile_uuid=logged_in_profile_uuid,
            has_already_liked=_check_if_already_liked,
        )

    async def get_gig_list_by_uuid(self, gig_list_uuid: UUID) -> GigListOut:
        gig_list = await models.GigList.get(
            db_session=self.db_session,
            uuid=gig_list_uuid,
        )
        if not gig_list:
            raise HTTPException(status_code=404, detail="Gig_list not found!")

        return gig_list.to_pydantic()

    async def search_giglist(
        self,
        searcher_uuid: UUID,
        title: Optional[str],
        price: Optional[float],
        place: Optional[str],
        is_looking_for: bool,
        is_performer: bool,
        limit: int = 50,
        offset: int = 0,
        pro_user_only: bool = False,
    ) -> PaginatedResponse[GigListOut]:
        stmt = sa.select(models.GigList)
        if title:
            if not is_looking_for:
                stmt = stmt.where(
                    models.GigList.title.ilike(f"%{title}%"),
                    ~models.GigList.is_looking_for,
                )

            else:
                stmt = stmt.where(
                    models.GigList.title.ilike(f"%{title}%"),
                    models.GigList.is_looking_for,
                )

        if place:
            stmt = stmt.where(models.GigList.location.ilike(f"%{place}%"))
        if not is_performer:
            if price:
                stmt = stmt.where(models.GigList.wage_requested == price)

        stmt = stmt.order_by(
            models.GigList.title.ilike(f"{title}%").desc(),  # Starts-with match first
            models.GigList.title,  # Alphabetical order
        )
        total_count = sa.select(sa.func.count()).select_from(stmt.subquery())
        total = await self.db_session.scalar(total_count)
        result = await self.db_session.scalars(stmt)
        items = [result.to_pydantic() for result in result.all()]
        return PaginatedResponse[GigListOut](
            limit=limit,
            offset=offset,
            total=total or 0,
            items=items,
        )

    async def get_my_favorite_gig_list(
        self, logged_in_profile_uuid: UUID, profile_uuid: UUID
    ) -> List[GigListOut]:
        # join with gig_list_like_many_to_many

        stmt = (
            sa.select(models.GigList)
            .join(
                models.gig_list_stars_many_to_many,
                models.GigList.uuid
                == models.gig_list_stars_many_to_many.c.gig_list_uuid,
            )
            .where(
                models.gig_list_stars_many_to_many.c.viewer_uuid == profile_uuid,
            )
            .order_by(
                models.GigList.created_at.desc(),
            )
        )

        result = await self.db_session.scalars(stmt)
        items = [result.to_pydantic() for result in result.all()]
        return items
