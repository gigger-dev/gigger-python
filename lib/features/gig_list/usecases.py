from typing import Optional
from uuid import UUID

from core.response import PaginatedResponse, SimpleResponse
from features.gig_list.repo import GigListRepo
from features.gig_list.schemas import GigListCreate, GigListOut, GigListUpdate


async def create_gig_list_usecase(repo: GigListRepo, body: GigListCreate) -> GigListOut:
    return await repo.create_gig_list(body)


async def list_gig_list_usecase(
    repo: GigListRepo, profile_uuid: UUID
) -> PaginatedResponse[GigListOut]:
    return await repo.list_gig_list(profile_uuid=profile_uuid)


async def list_recommended_gig_list_for_given_profile_usecase(
    repo: GigListRepo,
    profile_uuid: UUID,
    limit: int = 100,
    offset: int = 0,
) -> PaginatedResponse[GigListOut]:
    return await repo.list_recommended_gig_list_for_given_profile(
        profile_uuid=profile_uuid, limit=limit, offset=offset
    )


async def delete_git_list_usecase(
    repo: GigListRepo, gig_list_uuid: UUID, profile_uuid: UUID
) -> SimpleResponse:
    return await repo.delete_gig_list(
        gig_list_uuid=gig_list_uuid, profile_uuid=profile_uuid
    )


async def update_gig_list_usecase(repo: GigListRepo, body: GigListUpdate) -> GigListOut:
    return await repo.update_gig_list(body=body)


async def list_gig_list_by_profile_usecase(
    repo: GigListRepo, profile_uuid: UUID, viewer_profile_uuid: UUID
) -> list[GigListOut]:
    return await repo.list_gig_list_by_profile(
        profile_uuid=profile_uuid, viewer_profile_uuid=viewer_profile_uuid
    )


async def give_un_give_a_star_usecase(
    repo: GigListRepo,
    logged_in_profile_uuid: UUID,
    star_giver: UUID,
    gig_list_uuid: UUID,
):
    return await repo.give_star(
        logged_in_profile_uuid=logged_in_profile_uuid,
        star_giver=star_giver,
        gig_list_uuid=gig_list_uuid,
    )


async def get_gig_list_metadata_usecase(
    repo: GigListRepo,
    gig_list_uuid: UUID,
    logged_in_profile_uuid: UUID,
    viewer_uuid: UUID,
):
    return await repo.get_metadata(
        gig_list_uuid=gig_list_uuid,
        logged_in_profile_uuid=logged_in_profile_uuid,
        viewer_uuid=viewer_uuid,
    )


async def like_unlike_gig_list_usecase(
    repo: GigListRepo,
    logged_in_profile_uuid: UUID,
    liker_uuid: UUID,
    gig_list_uuid: UUID,
):
    return await repo.like_unlike_gig_list(
        logged_in_profile_uuid=logged_in_profile_uuid,
        liker_uuid=liker_uuid,
        gig_list_uuid=gig_list_uuid,
    )


async def get_gig_list_by_uuid_usecase(
    repo: GigListRepo, gig_list_uuid: UUID
) -> GigListOut:
    return await repo.get_gig_list_by_uuid(gig_list_uuid=gig_list_uuid)


async def search_giglist_usecase(
    repo: GigListRepo,
    searcher_uuid: UUID,
    title: Optional[str],
    price: Optional[float],
    place: Optional[str],
    is_performer: bool,
    is_looking_for: bool,
    limit: int = 50,
    offset: int = 0,
):
    return await repo.search_giglist(
        searcher_uuid=searcher_uuid,
        title=title,
        price=price,
        place=place,
        is_performer=is_performer,
        is_looking_for=is_looking_for,
        limit=limit,
        offset=offset,
    )


async def get_my_favorite_gig_list_usecase(
    repo: GigListRepo, profile_uuid: UUID, logged_in_profile_uuid: UUID
) -> list[GigListOut]:
    return await repo.get_my_favorite_gig_list(
        profile_uuid=profile_uuid, logged_in_profile_uuid=logged_in_profile_uuid
    )
