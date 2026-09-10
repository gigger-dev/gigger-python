import datetime
from abc import ABC, abstractmethod
from typing import List, Sequence
from uuid import UUID

import sqlalchemy as sa
from core.global_import import AsyncSession
from core.response import PaginatedResponse
from core.schemas import HashTag
from fastapi import HTTPException
from features.events.schemas import (
    EventIn,
    EventMetadata,
    EventOut,
    EventUpdate,
    LineUpAndPerformerIn,
)
from features.profile.models import Profile
from features.settings.models import Notification
from features.settings.schemas import (
    NotificationBodySchema,
    NotificationDataType,
    NotificationType,
)

from . import models


class EventRepo(ABC):
    @abstractmethod
    async def list(
        self,
        viewer_uuid: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> PaginatedResponse[EventOut]:
        pass

    @abstractmethod
    async def create(self, body: EventIn) -> EventOut:
        pass

    @abstractmethod
    async def update(self, body: EventUpdate, uuid: UUID) -> EventOut:
        pass

    @abstractmethod
    async def delete(self, uuid: UUID) -> bool:
        pass

    @abstractmethod
    async def get(self, uuid: UUID) -> EventOut:
        pass

    @abstractmethod
    async def search(
        self,
        keywords: str,
    ) -> List[EventOut]:
        pass

    @abstractmethod
    async def list_self_events(
        self,
        viewer_uuid: UUID,
    ) -> List[EventOut]:
        pass

    @abstractmethod
    async def list_events_by_profile_uuid(
        self,
        viewer_uuid: UUID,
        other_uuid: UUID,
    ) -> List[EventOut]:
        pass

    @abstractmethod
    async def event_accept(
        self,
        performer_uuid: UUID,
        event_uuid: UUID,
        creator_uuid: UUID,
    ) -> EventOut:
        pass

    @abstractmethod
    async def event_reject(
        self,
        performer_uuid: UUID,
        event_uuid: UUID,
        creator_uuid: UUID,
    ) -> EventOut:
        pass

    @abstractmethod
    async def view_event(
        self,
        logged_in_profile_uuid: UUID,
        viewer_uuid: UUID,
        event_uuid: UUID,
    ) -> EventMetadata:
        pass

    @abstractmethod
    async def get_metadata(
        self,
        event_uuid: UUID,
        logged_in_profile_uuid: UUID,
        viewer_uuid: UUID,
    ) -> EventMetadata:
        pass

    @abstractmethod
    async def like_unlike_event(
        self,
        logged_in_profile_uuid: UUID,
        liker_uuid: UUID,
        event_uuid: UUID,
    ) -> EventMetadata:
        pass

    @abstractmethod
    async def respond_event(
        self,
        logged_in_profile_uuid: UUID,
        responder_uuid: UUID,
        event_uuid: UUID,
        response: int,
    ) -> EventMetadata:
        pass


class EventRepoImpl(EventRepo):
    def __init__(self, db_session: AsyncSession) -> None:
        self._db_session = db_session

    async def list(
        self,
        viewer_uuid: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> PaginatedResponse[EventOut]:
        now = datetime.datetime.now(datetime.timezone.utc)

        stmt = (
            sa.select(models.Event)
            .where(
                models.Event.start_time > now,
            )
            .order_by(models.Event.start_time.desc())
        )
        total_stmt = sa.select(sa.func.count()).select_from(stmt.subquery())
        total = await self._db_session.scalar(
            total_stmt.limit(limit=limit).offset(offset)
        )
        result = await self._db_session.scalars(stmt.limit(limit=limit).offset(offset))
        items = [result.to_pydantic() for result in result.all()]
        return PaginatedResponse(
            total=total or 0,
            limit=limit,
            offset=offset,
            items=items,
        )

    async def _insert_line_n_performer(
        self, line_up_n_performers: List[LineUpAndPerformerIn], event: EventOut
    ):
        stmt = sa.insert(models.LineUpAndPerformer).values(
            [
                line.model_dump_with_event_uuid(event_uuid=event.uuid)
                for line in line_up_n_performers
            ]
        )
        await self._db_session.execute(stmt)
        await self._db_session.commit()
        await Notification.setup_and_send_notifications(
            db_session=self._db_session,
            profile_uuid_to_send_notification=[
                b.profile_uuid for b in line_up_n_performers
            ],
            notification_body=NotificationBodySchema(
                notification_type=NotificationType.NEW_REQUEST.value,
                notification_data_type=NotificationDataType.EVENT.value,
                profile_uuid=str(event.uuid),
                profile_name=event.name,
                profile_image=event.thumbnail_url,
                uuid=str(event.uuid),
            ),
            notification_data_type=NotificationDataType.EVENT,
        )

    async def _remove_line_n_performer(
        self, line_up_n_performers: List[LineUpAndPerformerIn], event_uuid: UUID
    ):
        stmt = sa.delete(models.LineUpAndPerformer).where(
            models.LineUpAndPerformer.event_uuid == event_uuid
        )
        await self._db_session.execute(stmt)
        await self._db_session.commit()

    async def _insert_hashtags(self, hashtags: List[HashTag], event_uuid: UUID):
        ## clean hashtags that have uuid
        hashtags_new = [h for h in hashtags if not h.uuid]
        hashtags_exist = [h for h in hashtags if h.uuid]
        new_hashtag_uuids: Sequence[UUID] = []
        if hashtags_new:
            stmt = (
                sa.insert(models.HashTag)
                .values([h.name for h in hashtags_new])
                .returning(
                    models.HashTag.uuid,
                )
            )
            result = await self._db_session.scalars(stmt)
            new_hashtag_uuids = result.all()
            await self._db_session.commit()
        all_hashtag_uuids = [h for h in new_hashtag_uuids] + [
            h.uuid for h in hashtags_exist if h.uuid
        ]

        if all_hashtag_uuids:
            stmt = (
                sa.insert(models.event_hashtags_many_to_many)
                .values(
                    [
                        {
                            "event_uuid": event_uuid,
                            "hashtag_uuid": h,
                        }
                        for h in all_hashtag_uuids
                    ]
                )
                .returning(models.event_hashtags_many_to_many.c.hashtag_uuid)
            )
            await self._db_session.execute(stmt)
            await self._db_session.commit()

    async def _remove_hashtags(
        self,
        event_uuid: UUID,
        hashtags: List[HashTag],
    ):
        stmt = sa.delete(models.event_hashtags_many_to_many).where(
            models.event_hashtags_many_to_many.c.hashtag_uuid.in_(
                [h.uuid for h in hashtags if h.uuid]
            )
        )
        await self._db_session.execute(stmt)
        await self._db_session.commit()

    async def _update_hashtags(self, event_uuid: UUID, hashtags: List[HashTag]):
        # remove all and add all again.
        stmt = sa.delete(models.event_hashtags_many_to_many).where(
            models.event_hashtags_many_to_many.c.event_uuid == event_uuid
        )
        await self._db_session.execute(stmt)

        await self._db_session.commit()
        if not hashtags:
            return

        await self._insert_hashtags(hashtags=hashtags, event_uuid=event_uuid)

    async def create(self, body: EventIn) -> EventOut:
        event = await models.Event.create(
            db_session=self._db_session,
            **body.model_dump(
                exclude={
                    "line_up_n_performers",
                    "hashtags",
                }
            ),
        )
        if not event:
            raise Exception("Even't can't be created.")
        if body.hashtags and event:
            await self._insert_hashtags(hashtags=body.hashtags, event_uuid=event.uuid)
        if body.line_up_n_performers and event:
            await self._insert_line_n_performer(
                line_up_n_performers=body.line_up_n_performers,
                event=event.to_pydantic(),
            )

        await self._db_session.refresh(event)
        return event.to_pydantic()

    async def update(self, body: EventUpdate, uuid: UUID) -> EventOut:
        stmt = (
            sa.update(models.Event)
            .where(models.Event.uuid == uuid)
            .values(
                body.model_dump(
                    exclude={
                        "line_up_n_performers_to_add",
                        "line_up_n_performers_to_remove",
                        "hashtags",
                    },
                    exclude_none=True,
                    exclude_defaults=True,
                )
            )
            .returning(models.Event)
        )
        event = await self._db_session.scalar(stmt)
        await self._db_session.commit()
        if body.line_up_n_performers_to_remove:
            await self._remove_line_n_performer(
                line_up_n_performers=body.line_up_n_performers_to_remove,
                event_uuid=uuid,
            )

        if body.line_up_n_performers_to_add and event:
            await self._insert_line_n_performer(
                line_up_n_performers=body.line_up_n_performers_to_add,
                event=event.to_pydantic(),
            )
        if body.hashtags and event:
            await self._update_hashtags(
                event_uuid=uuid,
                hashtags=body.hashtags,
            )

        # event = await models.Event.get(db_session=self._db_session, uuid=uuid)
        await self._db_session.refresh(event)

        if event:
            return event.to_pydantic()
        raise Exception("Something went wrong!")

    async def delete(self, uuid: UUID) -> bool:
        stmt = sa.delete(models.Event).where(models.Event.uuid == uuid)
        result = await self._db_session.execute(stmt)
        await self._db_session.commit()
        return result.rowcount > 0

    async def get(self, uuid: UUID) -> EventOut:
        event = await models.Event.get(db_session=self._db_session, uuid=uuid)
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        return event.to_pydantic()

    async def search(self, keywords: str) -> List[EventOut]:
        stmt = sa.select(models.Event).where(
            sa.or_(
                models.Event.name.ilike(f"%{keywords}%"),
                models.Event.description.ilike(f"%{keywords}%"),
                models.Event.location.ilike(f"%{keywords}%"),
                models.Event.genre.ilike(f"%{keywords}%"),
                models.Event.online_event_link.ilike(f"%{keywords}%"),
            )
        )
        result = await self._db_session.scalars(stmt)
        return [result.to_pydantic() for result in result.all()]

    async def list_self_events(self, viewer_uuid: UUID) -> List[EventOut]:
        stmt = sa.select(models.Event).where(
            models.Event.profile_uuid == viewer_uuid,
        )
        result = await self._db_session.scalars(stmt)
        return [result.to_pydantic() for result in result.all()]

    async def list_events_by_profile_uuid(
        self, viewer_uuid: UUID, other_uuid: UUID
    ) -> List[EventOut]:
        now = datetime.datetime.now(datetime.timezone.utc)

        stmt = (
            sa.select(models.Event)
            .where(
                models.Event.profile_uuid == other_uuid,
                models.Event.start_time > now,
            )
            .order_by(models.Event.start_time.desc())
        )
        result = await self._db_session.scalars(stmt)
        return [result.to_pydantic() for result in result.all()]

    async def event_accept(
        self, performer_uuid: UUID, event_uuid: UUID, creator_uuid: UUID
    ) -> EventOut:
        event = await models.Event.get(db_session=self._db_session, uuid=event_uuid)
        if not event:
            raise ValueError("Event not found")
        performer = await Profile.get(db_session=self._db_session, uuid=performer_uuid)
        if not performer:
            raise ValueError("Performer not found")
        stmt = (
            sa.update(models.LineUpAndPerformer)
            .where(models.LineUpAndPerformer.profile_uuid == performer_uuid)
            .where(models.LineUpAndPerformer.event_uuid == event_uuid)
            .values(is_accepted=True)
        )
        await self._db_session.execute(stmt)
        await self._db_session.commit()
        await Notification.setup_and_send_notifications(
            db_session=self._db_session,
            profile_uuid_to_send_notification=[creator_uuid],
            notification_body=NotificationBodySchema(
                notification_type=NotificationType.REQUEST_ACCEPTED.value,
                notification_data_type=NotificationDataType.EVENT.value,
                profile_uuid=str(performer.uuid),
                profile_name=str(performer.account.username),
                profile_image=str(performer.avatar_media),
                uuid=str(event.uuid),
            ),
            notification_data_type=NotificationDataType.EVENT,
        )
        delete_stmt = sa.delete(Notification).where(
            Notification.profile_uuid == performer_uuid,
            Notification.notification_type == 12,
        )
        await self._db_session.execute(delete_stmt)
        await self._db_session.commit()
        await self._db_session.refresh(event)
        return event.to_pydantic()

    async def event_reject(
        self, performer_uuid: UUID, event_uuid: UUID, creator_uuid: UUID
    ) -> EventOut:
        event = await models.Event.get(db_session=self._db_session, uuid=event_uuid)
        if not event:
            raise ValueError("Event not found")
        performer = await Profile.get(db_session=self._db_session, uuid=performer_uuid)
        if not performer:
            raise ValueError("Performer not found")

        stmt = sa.delete(models.LineUpAndPerformer).where(
            models.LineUpAndPerformer.profile_uuid == performer_uuid,
            models.LineUpAndPerformer.event_uuid == event_uuid,
        )
        await self._db_session.execute(stmt)
        await self._db_session.commit()
        await Notification.setup_and_send_notifications(
            db_session=self._db_session,
            profile_uuid_to_send_notification=[creator_uuid],
            notification_body=NotificationBodySchema(
                notification_type=NotificationType.REQUEST_REJECTED.value,
                notification_data_type=NotificationDataType.EVENT.value,
                profile_uuid=str(performer.uuid),
                profile_name=str(performer.account.username),
                profile_image=str(performer.avatar_media),
                uuid=str(event.uuid),
            ),
            notification_data_type=NotificationDataType.EVENT,
        )
        delete_stmt = sa.delete(Notification).where(
            Notification.profile_uuid == performer_uuid,
            Notification.notification_type == 12,
        )
        await self._db_session.execute(delete_stmt)
        await self._db_session.commit()
        await self._db_session.refresh(event)
        return event.to_pydantic()

    async def get_metadata(
        self,
        event_uuid: UUID,
        logged_in_profile_uuid: UUID,
        viewer_uuid: UUID,
        has_already_viewed: bool | None = None,
        has_already_liked: bool | None = None,
        response: int = 0,
    ) -> EventMetadata:
        event = await models.Event.get(db_session=self._db_session, uuid=event_uuid)
        _check_if_already_liked = has_already_liked
        if not _check_if_already_liked:
            _check_if_already_liked = await self._check_if_already_liked(
                event_uuid=event_uuid, liker_uuid=viewer_uuid
            )
        total_like_stmt = (
            sa.select(sa.func.count())
            .select_from(models.event_like_many_to_many)
            .where(
                models.event_like_many_to_many.c.event_uuid == event_uuid,
            )
        )
        total_like = await self._db_session.scalar(total_like_stmt)
        total_going = await self._get_going_response_count(
            db_session=self._db_session, event_uuid=event_uuid
        )
        _check_if_already_viewed = has_already_viewed
        if not _check_if_already_viewed:
            _check_if_already_viewed = await self._check_if_already_viewed(
                event_uuid=event_uuid, viewer_uuid=viewer_uuid
            )

        query = sa.select(models.event_response_many_to_many.c.response).where(
            models.event_response_many_to_many.c.event_uuid == event_uuid,
            models.event_response_many_to_many.c.responder_uuid == viewer_uuid,
        )

        result = await self._db_session.scalar(query)
        stmt1 = (
            sa.select(Profile)
            .join(
                models.event_response_many_to_many,
                models.event_response_many_to_many.c.responder_uuid == Profile.uuid,
            )
            .where(
                models.event_response_many_to_many.c.event_uuid == event_uuid,
                models.event_response_many_to_many.c.response == 1,
            )
        ).limit(5)
        going = await self._db_session.execute(stmt1)
        going_profiles = going.scalars().all()

        if not event:
            raise HTTPException(
                status_code=404,
                detail="Event not found!",
            )

        return EventMetadata(
            has_already_liked=_check_if_already_liked or False,
            like_count=total_like or 0,
            has_already_viewed=_check_if_already_viewed or False,
            response_type=result or 0,
            total_going_response=total_going or 0,
            going_profile=[
                profile.to_pydantic_fewer_details() for profile in going_profiles
            ],
        )

    async def _check_if_already_viewed(self, event_uuid: UUID, viewer_uuid: UUID):
        is_already_viewed_stmt = (
            sa.select(sa.func.count())
            .select_from(models.event_views_many_to_many)
            .where(
                models.event_views_many_to_many.c.event_uuid == event_uuid,
                models.event_views_many_to_many.c.viewer_uuid == viewer_uuid,
            )
        )
        count = await self._db_session.scalar(is_already_viewed_stmt)
        return count is not None and count > 0

    async def _get_like_count(self, db_session: AsyncSession, event_uuid: UUID):
        stmt = (
            sa.select(sa.func.count())
            .select_from(models.event_like_many_to_many)
            .where(
                models.event_like_many_to_many.c.event_uuid == event_uuid,
            )
        )
        return await db_session.scalar(stmt)

    async def _check_if_already_liked(self, event_uuid: UUID, liker_uuid: UUID):
        is_already_liked_stmt = (
            sa.select(sa.func.count())
            .select_from(models.event_like_many_to_many)
            .where(
                models.event_like_many_to_many.c.event_uuid == event_uuid,
                models.event_like_many_to_many.c.liker_uuid == liker_uuid,
            )
        )
        count = await self._db_session.scalar(is_already_liked_stmt)
        return count is not None and count > 0

    async def _get_going_response_count(
        self, db_session: AsyncSession, event_uuid: UUID
    ):
        stmt = (
            sa.select(sa.func.count())
            .select_from(models.event_response_many_to_many)
            .where(
                models.event_response_many_to_many.c.event_uuid == event_uuid,
                models.event_response_many_to_many.c.response == 1,
            )
        )
        return await db_session.scalar(stmt)

    async def view_event(
        self, logged_in_profile_uuid: UUID, viewer_uuid: UUID, event_uuid: UUID
    ) -> EventMetadata:
        _check_if_already_viewed = await self._check_if_already_viewed(
            event_uuid=event_uuid, viewer_uuid=viewer_uuid
        )
        if not _check_if_already_viewed:
            stmt = sa.insert(models.event_views_many_to_many).values(
                event_uuid=event_uuid, viewer_uuid=viewer_uuid
            )
            await self._db_session.execute(stmt)
            await self._db_session.commit()
            _check_if_already_viewed = True

        return await self.get_metadata(
            event_uuid=event_uuid,
            viewer_uuid=viewer_uuid,
            logged_in_profile_uuid=logged_in_profile_uuid,
            has_already_viewed=_check_if_already_viewed,
        )

    async def like_unlike_event(
        self, logged_in_profile_uuid: UUID, liker_uuid: UUID, event_uuid: UUID
    ) -> EventMetadata:
        _check_if_already_liked = await self._check_if_already_liked(
            event_uuid=event_uuid, liker_uuid=liker_uuid
        )
        if not _check_if_already_liked:
            stmt = sa.insert(models.event_like_many_to_many).values(
                event_uuid=event_uuid, liker_uuid=liker_uuid
            )
            await self._db_session.execute(stmt)
            await self._db_session.commit()

            event = await models.Event.get(
                db_session=self._db_session,
                uuid=event_uuid,
            )
            if not event:
                raise HTTPException(status_code=404, detail="Event not found!")
            liker_profile = await Profile.get(
                db_session=self._db_session, uuid=liker_uuid
            )
            if not liker_profile:
                raise HTTPException(status_code=404, detail="Profile not found!")
            if event.profile_uuid != liker_uuid:
                await Notification.setup_and_send_notifications(
                    db_session=self._db_session,
                    profile_uuid_to_send_notification=[event.profile_uuid],
                    notification_body=NotificationBodySchema(
                        notification_type=NotificationType.NEW_LIKE.value,
                        notification_data_type=NotificationDataType.EVENT.value,
                        profile_uuid=str(liker_profile.uuid),
                        profile_name=str(liker_profile.account.username),
                        profile_image=str(liker_profile.avatar_media),
                        uuid=str(event.uuid),
                    ),
                    notification_data_type=NotificationDataType.EVENT,
                )
            _check_if_already_liked = True
        else:
            stmt = sa.delete(models.event_like_many_to_many).where(
                models.event_like_many_to_many.c.event_uuid == event_uuid,
                models.event_like_many_to_many.c.liker_uuid == liker_uuid,
            )
            await self._db_session.execute(stmt)
            await self._db_session.commit()
            _check_if_already_liked = False

        return await self.get_metadata(
            event_uuid=event_uuid,
            viewer_uuid=liker_uuid,
            logged_in_profile_uuid=logged_in_profile_uuid,
            has_already_liked=_check_if_already_liked,
        )

    async def respond_event(
        self,
        logged_in_profile_uuid: UUID,
        responder_uuid: UUID,
        event_uuid: UUID,
        response: int,
    ) -> EventMetadata:
        stmt = None
        if self._db_session.bind.dialect.name == "postgresql":
            import sqlalchemy.dialects.postgresql as pa

            stmt = (
                pa.insert(models.event_response_many_to_many)
                .values(
                    event_uuid=event_uuid,
                    responder_uuid=responder_uuid,
                    response=response,
                )
                .on_conflict_do_update(
                    index_elements=["event_uuid", "responder_uuid"],
                    set_={"response": response},
                )
                .returning(models.event_response_many_to_many.c.response)
            )
        elif self._db_session.bind.dialect.name == "sqlite":
            import sqlalchemy.dialects.sqlite as sa

            stmt = (
                sa.insert(models.event_response_many_to_many)
                .values(
                    event_uuid=event_uuid,
                    responder_uuid=responder_uuid,
                    response=response,
                )
                .on_conflict_do_update(
                    index_elements=["event_uuid", "responder_uuid"],
                    set_={"response": response},
                )
                .returning(models.event_response_many_to_many.c.response)
            )
        else:
            raise HTTPException(status_code=500, detail="Unsupported database dialect.")

        try:
            result = await self._db_session.scalar(stmt)
            await self._db_session.commit()

            if result is None:
                raise HTTPException(status_code=404, detail="Event response not found!")

            return await self.get_metadata(
                event_uuid=event_uuid,
                viewer_uuid=responder_uuid,
                logged_in_profile_uuid=logged_in_profile_uuid,
                response=int(result),
            )

        except Exception as e:
            await self._db_session.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"An error occurred while responding to the event: {str(e)}",
            )
