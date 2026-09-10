from uuid import UUID

from core import schemas as core_schemas
from core.global_import import AsyncSession
from core.response import PaginatedResponse, SimpleResponse
from features.post import schemas
from features.post.repo import PostRepoImpl
from features.post.usecase import (
    create_post_usecase,
    get_all_post_usecase,
    get_post_by_uuid_usecase,
    get_post_metadata_usecase,
    like_unlike_post_usecase,
    list_post_for_given_profile_usecase,
    search_all_usecase,
    search_hash_tags_usecase,
    search_post_usecase,
    upsert_post_position_metadata_usecase,
    view_post_usecase,
)


class PostController:
    def __init__(self, db_session: AsyncSession):
        self.repo = PostRepoImpl(db_session=db_session)

    async def create_post(self, body: schemas.PostCreate) -> schemas.PostOut:
        return await create_post_usecase(repo=self.repo, body=body)

    async def search_hash_tags(self, query: str) -> list[core_schemas.HashTag]:
        return await search_hash_tags_usecase(repo=self.repo, query=query)

    async def list_self_posts(
        self, profile_uuid: UUID
    ) -> PaginatedResponse[schemas.PostOut]:
        return await self.repo.list_posts(profile_uuid=profile_uuid)

    async def delete_post(self, post_uuid: UUID, profile_uuid: UUID) -> SimpleResponse:
        return await self.repo.delete_post(
            post_uuid=post_uuid, profile_uuid=profile_uuid
        )

    async def update_post(self, body: schemas.PostUpdate) -> schemas.PostOut:
        return await self.repo.update_post(body=body)

    async def list_post_for_given_profile(
        self, profile_uuid: UUID, limit: int = 100, offset: int = 0
    ):
        return await list_post_for_given_profile_usecase(
            repo=self.repo, profile_uuid=profile_uuid, limit=limit, offset=offset
        )

    async def list_others_posts(
        self, profile_uuid: UUID, viewer_profile_uuid: UUID
    ) -> list[schemas.PostOut]:
        return await self.repo.list_others_posts(
            profile_uuid=profile_uuid, viewer_profile_uuid=viewer_profile_uuid
        )

    async def upsert_post_position_metadata(
        self, body: schemas.PostPositionMetadata
    ) -> schemas.PostPositionMetadata:
        return await upsert_post_position_metadata_usecase(repo=self.repo, body=body)

    async def get_layout(self, profile_uuid: UUID) -> schemas.PostPositionMetadata:
        return await self.repo.get_layout(profile_uuid=profile_uuid)

    async def get_post_metadata(
        self,
        post_uuid: UUID,
        logged_in_profile_uuid: UUID,
        viewer_uuid: UUID,
    ):
        return await get_post_metadata_usecase(
            repo=self.repo,
            post_uuid=post_uuid,
            logged_in_profile_uuid=logged_in_profile_uuid,
            viewer_uuid=viewer_uuid,
        )

    async def view_post(
        self,
        logged_in_profile_uuid: UUID,
        viewer_uuid: UUID,
        post_uuid: UUID,
    ):
        return await view_post_usecase(
            repo=self.repo,
            logged_in_profile_uuid=logged_in_profile_uuid,
            viewer_uuid=viewer_uuid,
            post_uuid=post_uuid,
        )

    async def get_post_by_uuid(self, post_uuid: UUID):
        return await get_post_by_uuid_usecase(repo=self.repo, post_uuid=post_uuid)

    async def like_unlike_post(
        self,
        logged_in_profile_uuid: UUID,
        liker_uuid: UUID,
        post_uuid: UUID,
    ):
        return await like_unlike_post_usecase(
            repo=self.repo,
            logged_in_profile_uuid=logged_in_profile_uuid,
            liker_uuid=liker_uuid,
            post_uuid=post_uuid,
        )

    async def search_post(
        self,
        searcher_uuid: UUID,
        title: str,
        keywords: str,
        genre: core_schemas.HashTag | None,
        limit: int,
        offset: int,
    ):
        return await search_post_usecase(
            repo=self.repo,
            searcher_uuid=searcher_uuid,
            title=title,
            keywords=keywords,
            genre=genre,
            limit=limit,
            offset=offset,
        )

    async def search_all(
        self,
        searcher_uuid: UUID,
        keywords: str,
    ):
        return await search_all_usecase(
            repo=self.repo,
            searcher_uuid=searcher_uuid,
            keywords=keywords,
        )

    async def get_all_post(self, profile_uuid: UUID):
        return await get_all_post_usecase(repo=self.repo, profile_uuid=profile_uuid)
