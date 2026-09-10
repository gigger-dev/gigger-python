from typing import Optional
from uuid import UUID

from core.global_import import AsyncSession
from core.response import PaginatedResponse, SimpleResponse
from features.gig_list.repo import GigListRepoImpl
from features.gig_list.schemas import GigListCreate, GigListOut, GigListUpdate
from features.gig_list.usecases import (
    create_gig_list_usecase,
    delete_git_list_usecase,
    get_gig_list_by_uuid_usecase,
    get_gig_list_metadata_usecase,
    get_my_favorite_gig_list_usecase,
    give_un_give_a_star_usecase,
    like_unlike_gig_list_usecase,
    list_gig_list_by_profile_usecase,
    list_gig_list_usecase,
    list_recommended_gig_list_for_given_profile_usecase,
    search_giglist_usecase,
    update_gig_list_usecase,
)


class GigListController:
    def __init__(self, db_session: AsyncSession) -> None:
        self.repo = GigListRepoImpl(db_session=db_session)

    async def create_gig_list(self, body: GigListCreate) -> GigListOut:
        return await create_gig_list_usecase(repo=self.repo, body=body)

    async def list_gig_list(self, profile_uuid: UUID) -> PaginatedResponse[GigListOut]:
        return await list_gig_list_usecase(repo=self.repo, profile_uuid=profile_uuid)

    async def list_recommended_gig_list_for_given_profile(
        self, profile_uuid: UUID, limit: int = 100, offset: int = 0
    ) -> PaginatedResponse[GigListOut]:
        return await list_recommended_gig_list_for_given_profile_usecase(
            repo=self.repo, profile_uuid=profile_uuid, limit=limit, offset=offset
        )

    async def delete_gig_list(
        self, gig_list_uuid: UUID, profile_uuid: UUID
    ) -> SimpleResponse:
        return await delete_git_list_usecase(
            repo=self.repo, gig_list_uuid=gig_list_uuid, profile_uuid=profile_uuid
        )

    async def update_gig_list(self, body: GigListUpdate) -> GigListOut:
        return await update_gig_list_usecase(repo=self.repo, body=body)

    async def list_gig_list_by_profile(
        self, profile_uuid: UUID, viewer_profile_uuid: UUID
    ) -> list[GigListOut]:
        return await list_gig_list_by_profile_usecase(
            repo=self.repo,
            profile_uuid=profile_uuid,
            viewer_profile_uuid=viewer_profile_uuid,
        )

    async def give_un_give_a_star(
        self,
        logged_in_profile_uuid: UUID,
        star_giver: UUID,
        gig_list_uuid: UUID,
    ):
        return await give_un_give_a_star_usecase(
            repo=self.repo,
            logged_in_profile_uuid=logged_in_profile_uuid,
            star_giver=star_giver,
            gig_list_uuid=gig_list_uuid,
        )

    async def get_gig_list_metadata(
        self,
        gig_list_uuid: UUID,
        logged_in_profile_uuid: UUID,
        viewer_uuid: UUID,
    ):
        return await get_gig_list_metadata_usecase(
            repo=self.repo,
            gig_list_uuid=gig_list_uuid,
            logged_in_profile_uuid=logged_in_profile_uuid,
            viewer_uuid=viewer_uuid,
        )

    async def like_unlike_gig_list(
        self,
        logged_in_profile_uuid: UUID,
        liker_uuid: UUID,
        gig_list_uuid: UUID,
    ):
        return await like_unlike_gig_list_usecase(
            repo=self.repo,
            logged_in_profile_uuid=logged_in_profile_uuid,
            liker_uuid=liker_uuid,
            gig_list_uuid=gig_list_uuid,
        )

    async def get_gig_list_by_uuid(self, gig_list_uuid: UUID):
        return await get_gig_list_by_uuid_usecase(
            repo=self.repo, gig_list_uuid=gig_list_uuid
        )

    async def search_giglist(
        self,
        searcher_uuid: UUID,
        title: Optional[str],
        price: Optional[float],
        place: Optional[str],
        is_performer: bool,
        is_looking_for: bool,
        limit: int = 50,
        offset: int = 0,
        pro_user_only: bool = False,
    ):
        return await search_giglist_usecase(
            repo=self.repo,
            searcher_uuid=searcher_uuid,
            title=title,
            price=price,
            place=place,
            is_performer=is_performer,
            is_looking_for=is_looking_for,
            limit=limit,
            offset=offset,
        )

    async def get_my_favorite_gig_list(
        self, profile_uuid: UUID, logged_in_profile_uuid: UUID
    ):
        return await get_my_favorite_gig_list_usecase(
            repo=self.repo,
            profile_uuid=profile_uuid,
            logged_in_profile_uuid=logged_in_profile_uuid,
        )
