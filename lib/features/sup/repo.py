import datetime
import logging
from abc import ABC, abstractmethod
from typing import List
from uuid import UUID

import sqlalchemy as sa
from core.config import settings
from core.fileupload import delete_file_from_s3
from core.global_import import AsyncSession
from core.response import PaginatedResponse, SimpleResponse
from fastapi import HTTPException
from features.profile import models as profile_models
from features.profile.schemas import ProfileFewerDetailsOut
from features.settings.models import Notification
from features.settings.schemas import (
    NotificationBodySchema,
    NotificationDataType,
    NotificationIn,
    NotificationType,
)
from features.sup import models, schemas


class SupRepo(ABC):
    @abstractmethod
    async def create_sup(self, body: schemas.SupCreate) -> schemas.SupOut:
        pass

    @abstractmethod
    async def list_sup_by_profile(
        self, profile_uuid: UUID, created_from: schemas.SupCreatedFromEnum
    ) -> List[schemas.SupOut]:
        pass

    @abstractmethod
    async def list_profile_having_sup(
        self,
        profile_uuid: UUID,
        limit: int,
        offset: int,
        created_from: schemas.SupCreatedFromEnum,
    ) -> PaginatedResponse[ProfileFewerDetailsOut]:
        pass

    @abstractmethod
    async def delete_sup(self, sup_uuid: UUID, profile_uuid: UUID) -> SimpleResponse:
        pass

    @abstractmethod
    async def like_unlike_sup(
        self,
        logged_in_profile_uuid: UUID,
        liker_uuid: UUID,
        sup_uuid: UUID,
    ) -> schemas.SupMetadata:
        pass

    @abstractmethod
    async def get_metadata(
        self,
        sup_uuid: UUID,
        logged_in_profile_uuid: UUID,
        viewer_uuid: UUID,
    ) -> schemas.SupMetadata:
        pass

    @abstractmethod
    async def share_sup(
        self,
        logged_in_profile_uuid: UUID,
        sharer_uuid: UUID,
        sup_uuid: UUID,
    ) -> schemas.SupMetadata:
        pass

    @abstractmethod
    async def get_sup_by_uuid(
        self,
        sup_uuid: UUID,
    ) -> schemas.SupOut:
        pass

    @abstractmethod
    async def view_sup(
        self,
        logged_in_profile_uuid: UUID,
        viewer_uuid: UUID,
        sup_uuid: UUID,
    ) -> schemas.SupMetadata:
        pass


class SupRepoImpl(SupRepo):
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def _upsert_tagged_profile(
        self,
        tagged_profiles: List[UUID],
        sup: models.Sup,
        is_update: bool = False,
    ):
        if self.db_session.bind.dialect.name == "postgresql":
            import sqlalchemy.dialects.postgresql as pa

            stmt = (
                pa.insert(models.sup_mentions_many_to_many)
                .values(
                    [
                        {"sub_uuid": sup.uuid, "profile_uuid": s_uid}
                        for s_uid in tagged_profiles
                    ]
                )
                .on_conflict_do_nothing(
                    index_elements=["sub_uuid", "profile_uuid"],
                )
            )
        elif self.db_session.bind.dialect.name == "sqlite":
            import sqlalchemy.dialects.sqlite as sa

            stmt = (
                sa.insert(models.sup_mentions_many_to_many)
                .values(
                    [
                        {"sub_uuid": sup.uuid, "profile_uuid": p_uid}
                        for p_uid in tagged_profiles
                    ]
                )
                .on_conflict_do_nothing(
                    index_elements=["sub_uuid", "profile_uuid"],
                )
            )
        else:
            raise HTTPException(status_code=500, detail="Unsupported database dialect.")
        await self.db_session.execute(stmt)
        await self.db_session.commit()
        profile = await profile_models.Profile.get(
            db_session=self.db_session, uuid=sup.profile_uuid
        )
        if not profile:
            logging.warning(f"No Profile({sup.profile_uuid}) ${sup.uuid}.")

        else:
            if is_update:
                return
            await Notification.setup_and_send_notifications(
                db_session=self.db_session,
                profile_uuid_to_send_notification=[b for b in tagged_profiles],
                notification_body=NotificationBodySchema(
                    notification_type=NotificationType.NEW_MENTION.value,
                    notification_data_type=NotificationDataType.SUP.value,
                    profile_uuid=str(sup.profile_uuid),
                    profile_name=profile.account.username,
                    profile_image=profile.cover_media,
                    uuid=str(sup.uuid),
                ),
                notification_data_type=NotificationDataType.SUP,
            )

    async def create_sup(self, body: schemas.SupCreate):
        try:
            sup = await models.Sup.create(
                db_session=self.db_session,
                **body.model_dump(
                    exclude={"hashtags", "tagged_profiles", "uuid"},
                ),
            )
            if not sup:
                raise HTTPException(status_code=500, detail="Failed to create sup!")
            for hash_tag in body.hashtags:
                if not hash_tag.uuid:
                    hash_tag_created = await models.HashTag.create_if_not_exist(
                        db_session=self.db_session,
                        **hash_tag.model_dump(exclude_none=True),
                    )
                    if hash_tag_created:
                        sup.hashtags.append(hash_tag_created)

            for tagged_profile_uuid in body.tagged_profiles:
                await self._upsert_tagged_profile(
                    tagged_profiles=[tagged_profile_uuid], sup=sup
                )

            await self.db_session.flush()
            await self.db_session.commit()
            await self.db_session.refresh(sup)
            return sup.to_pydantic()

        except Exception as e:
            raise e

    async def list_sup_by_profile(
        self, profile_uuid: UUID, created_from: schemas.SupCreatedFromEnum
    ) -> List[models.SupOut]:
        """
        List all sup created by alls.

        Args:
            profile_uuid (UUID): _description_

        Returns:
            List[models.SupOut]: _description_
        """
        # 1. filter date > 24 hours
        time_limit = datetime.datetime.now(datetime.UTC) - datetime.timedelta(hours=24)
        stmt = sa.select(models.Sup).where(
            models.Sup.created_at > time_limit,
            models.Sup.profile_uuid == profile_uuid,
        )
        # Apply filter based on created_from
        if created_from != schemas.SupCreatedFromEnum.NONE:
            stmt = stmt.where(models.Sup.create_from == created_from.value)
        result = await self.db_session.scalars(stmt)
        return [result.to_pydantic() for result in result.all()]

    async def list_profile_having_sup(
        self,
        profile_uuid: UUID,
        limit: int,
        offset: int,
        created_from: schemas.SupCreatedFromEnum,
    ) -> PaginatedResponse[ProfileFewerDetailsOut]:
        time_limit: datetime.datetime = datetime.datetime.now(
            datetime.UTC
        ) - datetime.timedelta(hours=24)
        latest_sups_subq = (
            sa.select(
                models.Sup.profile_uuid,
                sa.func.max(models.Sup.created_at).label("latest_sup"),
            )
            .where(
                sa.and_(
                    models.Sup.created_at > time_limit,
                    sa.or_(
                        models.Sup.profile_uuid == profile_uuid,
                        models.Sup.profile_uuid.in_(
                            sa.select(
                                profile_models.profile_followers_many_to_many.c.profile_uuid
                            ).where(
                                profile_models.profile_followers_many_to_many.c.follower_uuid
                                == profile_uuid
                            )
                        ),
                    ),
                    *(
                        [models.Sup.create_from == created_from.value]
                        if created_from != schemas.SupCreatedFromEnum.NONE
                        else []
                    ),
                )
            )
            .group_by(models.Sup.profile_uuid)
            .subquery("latest_sups")
        )
        # Main query
        main_query = (
            sa.select(profile_models.Profile)
            .join(
                latest_sups_subq,
                profile_models.Profile.uuid == latest_sups_subq.c.profile_uuid,
            )
            .order_by(latest_sups_subq.c.latest_sup.desc())
            .limit(limit)
            .offset(offset)
        )
        # Count query
        count_query = sa.select(
            sa.func.count(sa.func.distinct(profile_models.Profile.uuid))
        ).join(
            latest_sups_subq,
            profile_models.Profile.uuid == latest_sups_subq.c.profile_uuid,
        )
        total = await self.db_session.scalar(count_query)
        rows = await self.db_session.scalars(main_query)

        items = [row.to_pydantic_fewer_details() for row in rows]
        return PaginatedResponse(
            total=total or 0,
            limit=limit,
            offset=offset,
            items=items,
        )

    async def delete_sup(self, sup_uuid: UUID, profile_uuid: UUID) -> SimpleResponse:
        sup = await models.Sup.get(
            db_session=self.db_session,
            uuid=sup_uuid,
            profile_uuid=profile_uuid,
        )
        if not sup:
            raise HTTPException(status_code=404, detail="S'up not found!")
        if not settings.debug:
            try:
                if sup.thumbnail_url:
                    await delete_file_from_s3(sup.thumbnail_url)
            except Exception as e:
                print(f"Error deleting thumbnail image {sup.thumbnail_url}: {e}")
            try:
                if sup.video_url:
                    await delete_file_from_s3(sup.video_url)
            except Exception as e:
                print(f"Error deleting video file {sup.video_url}: {e}")
        await sup.delete(db_session=self.db_session, uuid=sup_uuid)
        return SimpleResponse(message="S'up deleted successfully!", status_code=200)

    async def _get_like_count(self, db_session: AsyncSession, sup_uuid: UUID):
        stmt = (
            sa.select(sa.func.count())
            .select_from(models.sup_like_many_to_many)
            .where(
                models.sup_like_many_to_many.c.sup_uuid == sup_uuid,
            )
        )
        return await db_session.scalar(stmt)

    async def _check_if_already_liked(self, sup_uuid: UUID, liker_uuid: UUID):
        is_already_liked_stmt = (
            sa.select(sa.func.count())
            .select_from(models.sup_like_many_to_many)
            .where(
                models.sup_like_many_to_many.c.sup_uuid == sup_uuid,
                models.sup_like_many_to_many.c.viewer_uuid == liker_uuid,
            )
        )
        count = await self.db_session.scalar(is_already_liked_stmt)
        return count is not None and count > 0

    async def _get_share_count(self, db_session: AsyncSession, sup_uuid: UUID):
        stmt = (
            sa.select(sa.func.count())
            .select_from(models.sup_share_many_to_many)
            .where(
                models.sup_share_many_to_many.c.sup_uuid == sup_uuid,
            )
        )
        return await db_session.scalar(stmt)

    async def _check_if_already_shared(self, sup_uuid: UUID, sharer_uuid: UUID):
        is_already_shared_stmt = (
            sa.select(sa.func.count())
            .select_from(models.sup_share_many_to_many)
            .where(
                models.sup_share_many_to_many.c.sup_uuid == sup_uuid,
                models.sup_share_many_to_many.c.viewer_uuid == sharer_uuid,
            )
        )
        count = await self.db_session.scalar(is_already_shared_stmt)
        return count is not None and count > 0

    async def _get_view_count(self, db_session: AsyncSession, sup_uuid: UUID):
        stmt = (
            sa.select(sa.func.count())
            .select_from(models.sup_view_many_to_many)
            .where(
                models.sup_view_many_to_many.c.sup_uuid == sup_uuid,
            )
        )
        return await db_session.scalar(stmt)

    async def _check_if_already_viewed(self, sup_uuid: UUID, viewer_uuid: UUID):
        is_already_viewed_stmt = (
            sa.select(sa.func.count())
            .select_from(models.sup_view_many_to_many)
            .where(
                models.sup_view_many_to_many.c.sup_uuid == sup_uuid,
                models.sup_view_many_to_many.c.viewer_uuid == viewer_uuid,
            )
        )
        count = await self.db_session.scalar(is_already_viewed_stmt)
        return count is not None and count > 0

    async def like_unlike_sup(
        self, logged_in_profile_uuid: UUID, liker_uuid: UUID, sup_uuid: UUID
    ) -> schemas.SupMetadata:
        _check_if_already_liked = await self._check_if_already_liked(
            sup_uuid=sup_uuid, liker_uuid=liker_uuid
        )
        if not _check_if_already_liked:
            stmt = sa.insert(models.sup_like_many_to_many).values(
                sup_uuid=sup_uuid, viewer_uuid=liker_uuid
            )
            await self.db_session.execute(stmt)
            await self.db_session.commit()

            sup = await models.Sup.get(
                db_session=self.db_session,
                uuid=sup_uuid,
            )
            if not sup:
                raise HTTPException(status_code=404, detail="Sup not found!")
            liker_profile = await profile_models.Profile.get(
                db_session=self.db_session, uuid=liker_uuid
            )
            if not liker_profile:
                raise HTTPException(status_code=404, detail="Profile not found!")
            if sup.profile_uuid != liker_uuid:
                notification_body = NotificationBodySchema(
                    profile_uuid=str(liker_uuid),
                    notification_type=NotificationType.NEW_LIKE.value,
                    profile_image=str(liker_profile.avatar_media),
                    profile_name=str(liker_profile.account.username),
                    uuid=str(sup.uuid),
                )
                notification_in = NotificationIn(
                    title="New Like",
                    body=f"{liker_profile.account.username} liked your Sup!",
                    notification_type=NotificationType.NEW_LIKE.value,
                    profile_uuid=sup.profile_uuid,
                    data=notification_body.model_dump(),
                )
                notification_out = await Notification.create(
                    db_session=self.db_session, **notification_in.model_dump()
                )
                if notification_out and not settings.debug:
                    await notification_out.send_multicast_notification(
                        profile_uuid_to_send_notification=sup.profile_uuid,
                        db_session=self.db_session,
                    )

            _check_if_already_liked = True
        else:
            stmt = sa.delete(models.sup_like_many_to_many).where(
                models.sup_like_many_to_many.c.sup_uuid == sup_uuid,
                models.sup_like_many_to_many.c.viewer_uuid == liker_uuid,
            )
            await self.db_session.execute(stmt)
            await self.db_session.commit()
            _check_if_already_liked = False

        return await self.get_metadata(
            sup_uuid=sup_uuid,
            viewer_uuid=liker_uuid,
            logged_in_profile_uuid=logged_in_profile_uuid,
            has_already_liked=_check_if_already_liked,
        )

    async def get_metadata(
        self,
        sup_uuid: UUID,
        logged_in_profile_uuid: UUID,
        viewer_uuid: UUID,
        has_already_liked: bool | None = None,
        has_already_shared: bool | None = None,
        has_already_viewed: bool | None = None,
    ) -> schemas.SupMetadata:
        sup = await models.Sup.get(db_session=self.db_session, uuid=sup_uuid)
        _check_if_already_liked = has_already_liked
        if not _check_if_already_liked:
            _check_if_already_liked = await self._check_if_already_liked(
                sup_uuid=sup_uuid, liker_uuid=viewer_uuid
            )
        total_like_stmt = (
            sa.select(sa.func.count())
            .select_from(models.sup_like_many_to_many)
            .where(
                models.sup_like_many_to_many.c.sup_uuid == sup_uuid,
            )
        )
        total_like = await self.db_session.scalar(total_like_stmt)
        _check_if_already_shared = has_already_shared
        if not _check_if_already_shared:
            _check_if_already_shared = await self._check_if_already_shared(
                sup_uuid=sup_uuid, sharer_uuid=viewer_uuid
            )
        total_share_stmt = (
            sa.select(sa.func.count())
            .select_from(models.sup_share_many_to_many)
            .where(
                models.sup_share_many_to_many.c.sup_uuid == sup_uuid,
            )
        )
        total_share = await self.db_session.scalar(total_share_stmt)
        _check_if_already_viewed = has_already_viewed
        if not _check_if_already_viewed:
            _check_if_already_viewed = await self._check_if_already_viewed(
                sup_uuid=sup_uuid, viewer_uuid=viewer_uuid
            )
        total_view = await self._get_view_count(
            db_session=self.db_session, sup_uuid=sup_uuid
        )
        if not sup:
            raise HTTPException(
                status_code=400,
                detail="Sup not found!",
            )

        return schemas.SupMetadata(
            has_already_liked=_check_if_already_liked or False,
            like_count=total_like or 0,
            has_already_shared=_check_if_already_shared or False,
            share_count=total_share or 0,
            has_already_viewed=_check_if_already_viewed or False,
            view_count=total_view or 0,
        )

    async def share_sup(
        self, logged_in_profile_uuid: UUID, sharer_uuid: UUID, sup_uuid: UUID
    ) -> schemas.SupMetadata:
        _check_if_already_shared = await self._check_if_already_shared(
            sup_uuid=sup_uuid, sharer_uuid=sharer_uuid
        )
        if not _check_if_already_shared:
            stmt = sa.insert(models.sup_share_many_to_many).values(
                sup_uuid=sup_uuid, viewer_uuid=sharer_uuid
            )
            await self.db_session.execute(stmt)
            await self.db_session.commit()

            sup = await models.Sup.get(
                db_session=self.db_session,
                uuid=sup_uuid,
            )
            if not sup:
                raise HTTPException(status_code=404, detail="Sup not found!")
            sharer_profile = await profile_models.Profile.get(
                db_session=self.db_session, uuid=sharer_uuid
            )
            if not sharer_profile:
                raise HTTPException(status_code=404, detail="Profile not found!")
            notification_body = NotificationBodySchema(
                profile_uuid=str(sharer_uuid),
                notification_type=NotificationType.NEW_SHARE.value,
                profile_image=str(sharer_profile.avatar_media),
                profile_name=str(sharer_profile.account.username),
                uuid=str(sharer_profile.uuid),
            )
            notification_in = NotificationIn(
                title="New Share",
                body=f"{sharer_profile.account.username} shared your Sup!",
                notification_type=NotificationType.NEW_SHARE.value,
                profile_uuid=sup.profile_uuid,
                data=notification_body.model_dump(),
            )
            notification_out = await Notification.create(
                db_session=self.db_session, **notification_in.model_dump()
            )
            if notification_out and not settings.debug:
                await notification_out.send_multicast_notification(
                    profile_uuid_to_send_notification=sup.profile_uuid,
                    db_session=self.db_session,
                )

            _check_if_already_shared = True

        return await self.get_metadata(
            sup_uuid=sup_uuid,
            viewer_uuid=sharer_uuid,
            logged_in_profile_uuid=logged_in_profile_uuid,
            has_already_shared=_check_if_already_shared,
        )

    async def get_sup_by_uuid(self, sup_uuid: UUID) -> schemas.SupOut:
        sup = await models.Sup.get(
            db_session=self.db_session,
            uuid=sup_uuid,
        )
        if not sup:
            raise HTTPException(status_code=404, detail="Sup not found!")

        return sup.to_pydantic()

    async def view_sup(
        self, logged_in_profile_uuid: UUID, viewer_uuid: UUID, sup_uuid: UUID
    ) -> schemas.SupMetadata:
        _check_if_already_viewed = await self._check_if_already_viewed(
            sup_uuid=sup_uuid, viewer_uuid=viewer_uuid
        )
        if not _check_if_already_viewed:
            stmt = sa.insert(models.sup_view_many_to_many).values(
                sup_uuid=sup_uuid, viewer_uuid=viewer_uuid
            )
            await self.db_session.execute(stmt)
            await self.db_session.commit()
            _check_if_already_viewed = True

        return await self.get_metadata(
            sup_uuid=sup_uuid,
            viewer_uuid=viewer_uuid,
            logged_in_profile_uuid=logged_in_profile_uuid,
            has_already_viewed=_check_if_already_viewed,
        )
