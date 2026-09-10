from typing import Optional
from uuid import UUID

from core.cvb import cbv
from core.dependencies import get_db_session
from core.global_import import AsyncSession
from core.permissions import is_verified_user
from core.response import PaginatedResponse, SimpleResponse
from fastapi import APIRouter, Depends, Query
from features.accounts import models as account_models
from features.gig_list import schemas
from features.gig_list.controller import GigListController

gig_list_router = APIRouter(prefix="/api/v1/gig-list", tags=["GigLists"])


@cbv(gig_list_router)
class GigListAPIView:
    def __init__(
        self,
        db_session: AsyncSession = Depends(get_db_session),
        account: account_models.Account = Depends(is_verified_user),
    ) -> None:
        self.db_session = db_session
        self.account = account
        self.controller = GigListController(db_session=db_session)

    @gig_list_router.post("/", response_model=schemas.GigListOut)
    async def create_gig_list(self, body: schemas.GigListCreate) -> schemas.GigListOut:
        return await self.controller.create_gig_list(body=body)

    @gig_list_router.get("/", response_model=PaginatedResponse[schemas.GigListOut])
    async def list_gig_list(
        self,
    ) -> PaginatedResponse[schemas.GigListOut]:
        return await self.controller.list_gig_list(
            profile_uuid=self.account.profile.uuid
        )

    @gig_list_router.get(
        "/recommended-gig-list/",
        response_model=PaginatedResponse[schemas.GigListOut],
    )
    async def list_recommended_gig_list_for_given_profile(
        self,
        limit: int = Query(
            100, ge=1, le=1000, description="Number of items to fetch (1-1000)"
        ),
        offset: int = Query(0, ge=0, description="Number of items to skip (0 or more)"),
    ) -> PaginatedResponse[schemas.GigListOut]:
        return await self.controller.list_recommended_gig_list_for_given_profile(
            profile_uuid=self.account.profile.uuid, limit=limit, offset=offset
        )

    @gig_list_router.delete("/{gig_list_uuid}/", response_model=SimpleResponse)
    async def delete_gig_list(self, gig_list_uuid: UUID):
        return await self.controller.delete_gig_list(
            gig_list_uuid=gig_list_uuid, profile_uuid=self.account.profile.uuid
        )

    @gig_list_router.patch("/{gig_list_uuid}/", response_model=schemas.GigListOut)
    async def update_gig_list(self, gig_list_uuid: UUID, body: schemas.GigListUpdate):
        return await self.controller.update_gig_list(body=body)

    @gig_list_router.get("/{profile_uuid}/", response_model=list[schemas.GigListOut])
    async def list_gig_list_by_profile(self, profile_uuid: UUID):
        assert self.account.profile.uuid != profile_uuid, (
            "You can not call your own profile as viewer."
        )
        return await self.controller.list_gig_list_by_profile(
            profile_uuid=profile_uuid, viewer_profile_uuid=self.account.profile.uuid
        )

    @gig_list_router.post(
        "/{gig_list_uuid}/star/", response_model=schemas.GigListMetadata
    )
    async def give_un_give_a_star(
        self,
        star_giver_uuid: UUID,
        gig_list_uuid: UUID,
    ):
        return await self.controller.give_un_give_a_star(
            logged_in_profile_uuid=self.account.profile.uuid,
            star_giver=star_giver_uuid,
            gig_list_uuid=gig_list_uuid,
        )

    @gig_list_router.post(
        "/{gig_list_uuid}/metadata/", response_model=schemas.GigListMetadata
    )
    async def get_gig_list_metadata(
        self,
        gig_list_uuid: UUID,
        viewer_uuid: UUID,
    ):
        return await self.controller.get_gig_list_metadata(
            gig_list_uuid=gig_list_uuid,
            logged_in_profile_uuid=self.account.profile.uuid,
            viewer_uuid=viewer_uuid,
        )

    @gig_list_router.post(
        "/{gig_list_uuid}/like/", response_model=schemas.GigListMetadata
    )
    async def like_unlike_gig_list(
        self,
        liker_uuid: UUID,
        gig_list_uuid: UUID,
    ):
        return await self.controller.like_unlike_gig_list(
            logged_in_profile_uuid=self.account.profile.uuid,
            liker_uuid=liker_uuid,
            gig_list_uuid=gig_list_uuid,
        )

    @gig_list_router.get("/{gig_list_uuid}/get/", response_model=schemas.GigListOut)
    async def get_gig_list_by_uuid(self, gig_list_uuid: UUID):
        return await self.controller.get_gig_list_by_uuid(gig_list_uuid=gig_list_uuid)

    @gig_list_router.get("{profile_uuid}/fav/", response_model=list[schemas.GigListOut])
    async def get_my_fav_gig_list(
        self,
        profile_uuid: UUID,
    ):
        return await self.controller.get_my_favorite_gig_list(
            logged_in_profile_uuid=self.account.profile.uuid,
            profile_uuid=profile_uuid,
        )

    @gig_list_router.get(
        "/{searcher_uuid}/search/",
        response_model=PaginatedResponse[schemas.GigListOut],
    )
    async def search_giglist(
        self,
        searcher_uuid: UUID,
        title: Optional[str] = Query(None),
        price: Optional[float] = Query(None),
        place: Optional[str] = Query(None),
        is_performer: bool = False,
        is_looking_for: bool = False,
        limit: int = 50,
        offset: int = 0,
    ):
        return await self.controller.search_giglist(
            searcher_uuid=self.account.profile.uuid,
            title=title,
            price=price,
            place=place,
            is_performer=is_performer,
            is_looking_for=is_looking_for,
            limit=limit,
            offset=offset,
        )
