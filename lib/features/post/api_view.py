from typing import List
from uuid import UUID

from core import schemas as core_schema
from core.cvb import cbv
from core.dependencies import get_db_session
from core.global_import import AsyncSession
from core.permissions import is_verified_user
from core.response import PaginatedResponse, SimpleResponse
from fastapi import APIRouter, Depends, Query
from features.accounts import models as account_models
from features.post import schemas
from features.post.controller import PostController

post_router = APIRouter(prefix="/api/v1/posts", tags=["Posts"])


@cbv(post_router)
class PostAPIView:
    def __init__(
        self,
        db_session: AsyncSession = Depends(get_db_session),
        account: account_models.Account = Depends(is_verified_user),
    ) -> None:
        self.db_session = db_session
        self.account = account
        self.controller = PostController(db_session=db_session)

    @post_router.post("/", response_model=schemas.PostOut)
    async def create_post(self, body: schemas.PostCreate):
        return await self.controller.create_post(body=body)

    @post_router.get("/hashtags/", response_model=List[core_schema.HashTag])
    async def search_hash_tags(self, query: str):
        return await self.controller.search_hash_tags(query=query)

    @post_router.get("/fab/", response_model=PaginatedResponse[schemas.PostOut])
    async def list_self_posts(self, profile_uuid: UUID):
        return await self.controller.list_self_posts(profile_uuid=profile_uuid)

    @post_router.get("/{profile_uuid}/fab/", response_model=list[schemas.PostOut])
    async def list_others_fab9(self, profile_uuid: UUID):
        assert self.account.profile.uuid != profile_uuid, (
            "You can not call your own profile as viewer."
        )
        return await self.controller.list_others_posts(
            profile_uuid=profile_uuid, viewer_profile_uuid=self.account.profile.uuid
        )

    @post_router.delete("/{post_uuid}", response_model=SimpleResponse)
    async def delete_post(self, post_uuid: UUID):
        return await self.controller.delete_post(
            post_uuid=post_uuid, profile_uuid=self.account.profile.uuid
        )

    @post_router.patch("/{post_uuid}", response_model=schemas.PostOut)
    async def update_post(self, post_uuid: UUID, body: schemas.PostUpdate):
        return await self.controller.update_post(body=body)

    @post_router.get(
        "/recommended-post/", response_model=PaginatedResponse[schemas.PostOut]
    )
    async def list_recommended_posts_for_profile(
        self,
        limit: int = Query(
            100, ge=1, le=1000, description="Number of items to fetch (1-1000)"
        ),
        offset: int = Query(0, ge=0, description="Number of items to skip (0 or more)"),
    ):
        return await self.controller.list_post_for_given_profile(
            profile_uuid=self.account.profile.uuid, limit=limit, offset=offset
        )

    @post_router.post("/layout/", response_model=schemas.PostPositionMetadata)
    async def upsert_post_position_metadata(self, body: schemas.PostPositionMetadata):
        return await self.controller.upsert_post_position_metadata(body=body)

    @post_router.get("/layout/", response_model=schemas.PostPositionMetadata)
    async def get_layout(self, profile_uuid: UUID):
        return await self.controller.get_layout(profile_uuid=profile_uuid)

    @post_router.get("/{post_uuid}/metadata/", response_model=schemas.PostMetadata)
    async def get_post_metadata(
        self,
        post_uuid: UUID,
        viewer_uuid: UUID,
    ):
        return await self.controller.get_post_metadata(
            post_uuid=post_uuid,
            logged_in_profile_uuid=self.account.profile.uuid,
            viewer_uuid=viewer_uuid,
        )

    @post_router.post("/{post_uuid}/view/", response_model=schemas.PostMetadata)
    async def view_post(
        self,
        viewer_uuid: UUID,
        post_uuid: UUID,
    ):
        return await self.controller.view_post(
            logged_in_profile_uuid=self.account.profile.uuid,
            viewer_uuid=viewer_uuid,
            post_uuid=post_uuid,
        )

    @post_router.get("/{post_uuid}/get/", response_model=schemas.PostOut)
    async def get_post_by_uuid(self, post_uuid: UUID):
        return await self.controller.get_post_by_uuid(post_uuid=post_uuid)

    @post_router.post("/{post_uuid}/like/", response_model=schemas.PostMetadata)
    async def like_unlike_post(
        self,
        liker_uuid: UUID,
        post_uuid: UUID,
    ):
        return await self.controller.like_unlike_post(
            logged_in_profile_uuid=self.account.profile.uuid,
            liker_uuid=liker_uuid,
            post_uuid=post_uuid,
        )

    @post_router.get(
        "/{searcher_uuid}/search",
        response_model=PaginatedResponse[schemas.PostOut],
    )
    async def search_post(
        self,
        searcher_uuid: UUID,
        title: str,
        keywords: str,
        genre: str,
        limit: int = Query(
            50, ge=1, le=100, description="Number of items to fetch (1-100)"
        ),
        offset: int = Query(0, ge=0, description="Number of items to skip (0 or more)"),
    ):
        hashtag = None
        if genre:
            hashtag = core_schema.HashTag(name="", uuid=UUID(genre))

        return await self.controller.search_post(
            searcher_uuid=searcher_uuid,
            title=title,
            keywords=keywords,
            genre=hashtag,  # TODO need to refactor this.
            limit=limit,
            offset=offset,
        )

    @post_router.get(
        "/{searcher_uuid}/search/all/",
        response_model=schemas.AllSearchResults,
    )
    async def search_all(
        self,
        searcher_uuid: UUID,
        keywords: str,
    ):
        assert searcher_uuid == self.account.profile.uuid, (
            "Searcher UUID must be logged in profile UUID."
        )
        return await self.controller.search_all(
            searcher_uuid=self.account.profile.uuid, keywords=keywords
        )

    @post_router.get("/{profile_uuid}/posts/", response_model=list[schemas.PostOut])
    async def get_all_post(
        self,
        profile_uuid: UUID,
    ):
        return await self.controller.get_all_post(profile_uuid=profile_uuid)
