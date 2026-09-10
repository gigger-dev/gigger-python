from uuid import UUID

from core.global_import import AsyncSession
from core.response import BasicResponse
from features.events.repo import EventRepoImpl
from features.events.schemas import EventIn, EventUpdate
from features.events.usecase import (
    create_event_usecase,
    delete_event_usecase,
    event_accept_usecase,
    event_reject_usecase,
    get_event_metadata_usecase,
    get_event_usecase,
    like_unlike_event_usecase,
    list_events_by_profile_uuid_usecase,
    list_events_usecase,
    list_self_events_usecase,
    respond_event_usecase,
    search_event_usecase,
    update_event_usecase,
    view_event_usecase,
)


class EventController:
    def __init__(self, db_session: AsyncSession):
        self._db_session = db_session
        self._repo = EventRepoImpl(db_session=db_session)

    async def get_event(self, uuid: UUID):
        return await get_event_usecase(repo=self._repo, uuid=uuid)

    async def list_events(
        self,
        viewer_uuid: UUID,
        limit: int = 50,
        offset: int = 0,
    ):
        return await list_events_usecase(
            repo=self._repo, viewer_uuid=viewer_uuid, limit=limit, offset=offset
        )

    async def list_self_events(self, viewer_uuid: UUID):
        return await list_self_events_usecase(repo=self._repo, viewer_uuid=viewer_uuid)

    async def create_event(self, body: EventIn):
        return await create_event_usecase(repo=self._repo, body=body)

    async def update_event(self, body: EventUpdate, uuid: UUID):
        return await update_event_usecase(repo=self._repo, body=body, uuid=uuid)

    async def delete_event(self, uuid: UUID):
        result = await delete_event_usecase(repo=self._repo, uuid=uuid)
        return BasicResponse(
            message=f"Event deleted {'successfully' if result else 'failed. '}!",
            success=True,
        )

    async def search(self, keywords: str):
        return await search_event_usecase(repo=self._repo, keywords=keywords)

    async def list_events_by_profile_uuid(self, viewer_uuid: UUID, other_uuid: UUID):
        return await list_events_by_profile_uuid_usecase(
            repo=self._repo, viewer_uuid=viewer_uuid, other_uuid=other_uuid
        )

    async def event_accept(
        self, performer_uuid: UUID, event_uuid: UUID, creator_uuid: UUID
    ):
        return await event_accept_usecase(
            repo=self._repo,
            performer_uuid=performer_uuid,
            event_uuid=event_uuid,
            creator_uuid=creator_uuid,
        )

    async def event_reject(
        self, performer_uuid: UUID, event_uuid: UUID, creator_uuid: UUID
    ):
        return await event_reject_usecase(
            repo=self._repo,
            performer_uuid=performer_uuid,
            event_uuid=event_uuid,
            creator_uuid=creator_uuid,
        )

    async def view_event(
        self,
        logged_in_profile_uuid: UUID,
        viewer_uuid: UUID,
        event_uuid: UUID,
    ):
        return await view_event_usecase(
            repo=self._repo,
            logged_in_profile_uuid=logged_in_profile_uuid,
            viewer_uuid=viewer_uuid,
            event_uuid=event_uuid,
        )

    async def get_event_metadata(
        self,
        event_uuid: UUID,
        logged_in_profile_uuid: UUID,
        viewer_uuid: UUID,
    ):
        return await get_event_metadata_usecase(
            repo=self._repo,
            event_uuid=event_uuid,
            logged_in_profile_uuid=logged_in_profile_uuid,
            viewer_uuid=viewer_uuid,
        )

    async def like_unlike_event(
        self,
        logged_in_profile_uuid: UUID,
        liker_uuid: UUID,
        event_uuid: UUID,
    ):
        return await like_unlike_event_usecase(
            repo=self._repo,
            logged_in_profile_uuid=logged_in_profile_uuid,
            liker_uuid=liker_uuid,
            event_uuid=event_uuid,
        )

    async def respond_event(
        self,
        logged_in_profile_uuid: UUID,
        responder_uuid: UUID,
        event_uuid: UUID,
        response: int,
    ):
        return await respond_event_usecase(
            repo=self._repo,
            logged_in_profile_uuid=logged_in_profile_uuid,
            responder_uuid=responder_uuid,
            event_uuid=event_uuid,
            response=response,
        )
