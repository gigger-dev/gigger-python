from typing import List
from uuid import UUID

from core.response import PaginatedResponse, SimpleResponse
from features.profile.schemas import ProfileFewerDetailsOut
from features.sup import schemas
from features.sup.repo import SupRepo


async def create_sup_usecase(repo: SupRepo, body: schemas.SupCreate) -> schemas.SupOut:
    return await repo.create_sup(body=body)


async def list_sup_usecase(
    repo: SupRepo, profile_uuid: UUID, created_from: schemas.SupCreatedFromEnum
) -> List[schemas.SupOut]:
    return await repo.list_sup_by_profile(
        profile_uuid=profile_uuid, created_from=created_from
    )


async def list_profile_having_sup_usecase(
    repo: SupRepo,
    profile_uuid: UUID,
    limit: int,
    offset: int,
    created_from: schemas.SupCreatedFromEnum,
) -> PaginatedResponse[ProfileFewerDetailsOut]:
    return await repo.list_profile_having_sup(
        profile_uuid=profile_uuid, limit=limit, offset=offset, created_from=created_from
    )


async def delete_sup_usecase(
    repo: SupRepo, sup_uuid: UUID, profile_uuid: UUID
) -> SimpleResponse:
    return await repo.delete_sup(sup_uuid=sup_uuid, profile_uuid=profile_uuid)


async def like_unlike_sup_usecase(
    repo: SupRepo,
    logged_in_profile_uuid: UUID,
    liker_uuid: UUID,
    sup_uuid: UUID,
):
    return await repo.like_unlike_sup(
        logged_in_profile_uuid=logged_in_profile_uuid,
        liker_uuid=liker_uuid,
        sup_uuid=sup_uuid,
    )


async def get_sup_metadata_usecase(
    repo: SupRepo,
    sup_uuid: UUID,
    logged_in_profile_uuid: UUID,
    viewer_uuid: UUID,
):
    return await repo.get_metadata(
        sup_uuid=sup_uuid,
        logged_in_profile_uuid=logged_in_profile_uuid,
        viewer_uuid=viewer_uuid,
    )


async def share_sup_usecase(
    repo: SupRepo,
    logged_in_profile_uuid: UUID,
    sharer_uuid: UUID,
    sup_uuid: UUID,
):
    return await repo.share_sup(
        logged_in_profile_uuid=logged_in_profile_uuid,
        sharer_uuid=sharer_uuid,
        sup_uuid=sup_uuid,
    )


async def get_sup_by_uuid_usecase(repo: SupRepo, sup_uuid: UUID) -> schemas.SupOut:
    return await repo.get_sup_by_uuid(sup_uuid=sup_uuid)


async def view_sup_usecase(
    repo: SupRepo,
    logged_in_profile_uuid: UUID,
    viewer_uuid: UUID,
    sup_uuid: UUID,
):
    return await repo.view_sup(
        logged_in_profile_uuid=logged_in_profile_uuid,
        viewer_uuid=viewer_uuid,
        sup_uuid=sup_uuid,
    )
