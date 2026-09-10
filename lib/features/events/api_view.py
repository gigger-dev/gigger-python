from typing import List
from uuid import UUID

from core.cvb import cbv
from core.dependencies import get_db_session
from core.global_import import AsyncSession
from core.permissions import is_verified_user
from core.response import BasicResponse, PaginatedResponse
from fastapi import APIRouter, Depends, Query
from features.accounts import models as account_models
from features.events.controller import EventController
from features.events.schemas import EventIn, EventMetadata, EventOut, EventUpdate

event_router = APIRouter(prefix="/api/v1/events", tags=["Events"])


@cbv(event_router)
class EventAPIView:
    def __init__(
        self,
        db_session: AsyncSession = Depends(get_db_session),
        account: account_models.Account = Depends(is_verified_user),
    ) -> None:
        self._db_session = db_session
        self.account = account
        self.controller = EventController(db_session=db_session)

    @event_router.get("/", response_model=PaginatedResponse[EventOut])
    async def list_events(
        self,
        limit: int = Query(
            50,
            ge=1,
            le=100,
            description="Number of items to fetch (1-100)",
        ),
        offset: int = Query(0, ge=0, description="Number of items to skip (0 or more)"),
    ):
        return await self.controller.list_events(
            viewer_uuid=self.account.profile.uuid, limit=limit, offset=offset
        )

    @event_router.get("/self/", response_model=List[EventOut])
    async def list_self_events(
        self,
    ):
        return await self.controller.list_self_events(
            viewer_uuid=self.account.profile.uuid
        )

    @event_router.post("/", response_model=EventOut)
    async def create_event(self, body: EventIn):
        return await self.controller.create_event(body=body)

    @event_router.patch("/{event_uuid}/", response_model=EventOut)
    async def update_event(self, event_uuid: UUID, body: EventUpdate):
        return await self.controller.update_event(body=body, uuid=event_uuid)

    @event_router.delete("/{event_uuid}/", response_model=BasicResponse)
    async def delete_event(self, event_uuid: UUID):
        return await self.controller.delete_event(uuid=event_uuid)

    @event_router.get("/{event_uuid}/", response_model=EventOut)
    async def get_event(self, event_uuid: UUID):
        return await self.controller.get_event(uuid=event_uuid)

    @event_router.get("/{event_uuid}/metadata/", response_model=EventMetadata)
    async def get_event_metadata(
        self,
        event_uuid: UUID,
        viewer_uuid: UUID,
    ):
        return await self.controller.get_event_metadata(
            event_uuid=event_uuid,
            logged_in_profile_uuid=self.account.profile.uuid,
            viewer_uuid=viewer_uuid,
        )

    @event_router.post("/{event_uuid}/like/", response_model=EventMetadata)
    async def like_unlike_event(
        self,
        liker_uuid: UUID,
        event_uuid: UUID,
    ):
        return await self.controller.like_unlike_event(
            logged_in_profile_uuid=self.account.profile.uuid,
            liker_uuid=liker_uuid,
            event_uuid=event_uuid,
        )

    @event_router.post("/{event_uuid}/view/", response_model=EventMetadata)
    async def view_event(
        self,
        viewer_uuid: UUID,
        event_uuid: UUID,
    ):
        return await self.controller.view_event(
            logged_in_profile_uuid=self.account.profile.uuid,
            viewer_uuid=viewer_uuid,
            event_uuid=event_uuid,
        )

    @event_router.post("/{event_uuid}/respond/", response_model=EventMetadata)
    async def respond_event(
        self,
        responder_uuid: UUID,
        event_uuid: UUID,
        response: int,
    ):
        return await self.controller.respond_event(
            logged_in_profile_uuid=self.account.profile.uuid,
            responder_uuid=responder_uuid,
            event_uuid=event_uuid,
            response=response,
        )

    @event_router.get("/search/{searcher_uuid}/", response_model=List[EventOut])
    async def search(
        self,
        keywords: str,
    ):
        return await self.controller.search(keywords=keywords)

    @event_router.get(
        "/list/{profile_uuid}/",
        response_model=List[EventOut],
    )
    async def get_events_by_profile_uuid(self, profile_uuid: UUID):
        return await self.controller.list_events_by_profile_uuid(
            viewer_uuid=self.account.profile.uuid, other_uuid=profile_uuid
        )

    @event_router.post("/event_accept/{performer_uuid}/", response_model=EventOut)
    async def event_accept(
        self, performer_uuid: UUID, event_uuid: UUID, creator_uuid: UUID
    ):
        return await self.controller.event_accept(
            performer_uuid=performer_uuid,
            event_uuid=event_uuid,
            creator_uuid=creator_uuid,
        )

    @event_router.post("/event_reject/{performer_uuid}/", response_model=EventOut)
    async def event_reject(
        self, performer_uuid: UUID, event_uuid: UUID, creator_uuid: UUID
    ):
        return await self.controller.event_reject(
            performer_uuid=performer_uuid,
            event_uuid=event_uuid,
            creator_uuid=creator_uuid,
        )
