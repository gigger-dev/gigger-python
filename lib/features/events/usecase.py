from uuid import UUID

from features.events.repo import EventRepo
from features.events.schemas import EventIn, EventUpdate


async def create_event_usecase(repo: EventRepo, body: EventIn):
    return await repo.create(body=body)


async def update_event_usecase(repo: EventRepo, body: EventUpdate, uuid: UUID):
    return await repo.update(body=body, uuid=uuid)


async def delete_event_usecase(repo: EventRepo, uuid: UUID):
    return await repo.delete(uuid=uuid)


async def get_event_usecase(repo: EventRepo, uuid: UUID):
    return await repo.get(uuid=uuid)


async def search_event_usecase(repo: EventRepo, keywords: str):
    return await repo.search(keywords=keywords)


async def list_self_events_usecase(repo: EventRepo, viewer_uuid: UUID):
    return await repo.list_self_events(viewer_uuid=viewer_uuid)


async def list_events_usecase(
    repo: EventRepo,
    viewer_uuid: UUID,
    limit: int = 50,
    offset: int = 0,
):
    return await repo.list(viewer_uuid=viewer_uuid, limit=limit, offset=offset)


async def list_events_by_profile_uuid_usecase(
    repo: EventRepo, viewer_uuid: UUID, other_uuid: UUID
):
    return await repo.list_events_by_profile_uuid(
        viewer_uuid=viewer_uuid, other_uuid=other_uuid
    )


async def event_accept_usecase(
    repo: EventRepo, performer_uuid: UUID, event_uuid: UUID, creator_uuid: UUID
):
    return await repo.event_accept(
        performer_uuid=performer_uuid, event_uuid=event_uuid, creator_uuid=creator_uuid
    )


async def event_reject_usecase(
    repo: EventRepo, performer_uuid: UUID, event_uuid: UUID, creator_uuid: UUID
):
    return await repo.event_reject(
        performer_uuid=performer_uuid, event_uuid=event_uuid, creator_uuid=creator_uuid
    )


async def view_event_usecase(
    repo: EventRepo,
    logged_in_profile_uuid: UUID,
    viewer_uuid: UUID,
    event_uuid: UUID,
):
    return await repo.view_event(
        logged_in_profile_uuid=logged_in_profile_uuid,
        viewer_uuid=viewer_uuid,
        event_uuid=event_uuid,
    )


async def get_event_metadata_usecase(
    repo: EventRepo,
    event_uuid: UUID,
    logged_in_profile_uuid: UUID,
    viewer_uuid: UUID,
):
    return await repo.get_metadata(
        event_uuid=event_uuid,
        logged_in_profile_uuid=logged_in_profile_uuid,
        viewer_uuid=viewer_uuid,
    )


async def like_unlike_event_usecase(
    repo: EventRepo,
    logged_in_profile_uuid: UUID,
    liker_uuid: UUID,
    event_uuid: UUID,
):
    return await repo.like_unlike_event(
        logged_in_profile_uuid=logged_in_profile_uuid,
        liker_uuid=liker_uuid,
        event_uuid=event_uuid,
    )


async def respond_event_usecase(
    repo: EventRepo,
    logged_in_profile_uuid: UUID,
    responder_uuid: UUID,
    event_uuid: UUID,
    response: int,
):
    return await repo.respond_event(
        logged_in_profile_uuid=logged_in_profile_uuid,
        responder_uuid=responder_uuid,
        event_uuid=event_uuid,
        response=response,
    )
