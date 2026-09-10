from uuid import UUID

from core import schemas as core_schemas
from core.response import PaginatedResponse, SimpleResponse
from features.post import schemas
from features.post.repo import PostRepo


async def search_hash_tags_usecase(
    repo: PostRepo, query: str
) -> list[core_schemas.HashTag]:
    return await repo.search_hash_tags(query=query)


async def create_post_usecase(
    repo: PostRepo, body: schemas.PostCreate
) -> schemas.PostOut:
    return await repo.create_post(body=body)


async def list_self_post_usecase(
    repo: PostRepo, profile_uuid: UUID
) -> PaginatedResponse[schemas.PostOut]:
    return await repo.list_posts(profile_uuid=profile_uuid)


async def delete_post_usecase(
    repo: PostRepo, post_uuid: UUID, profile_uuid: UUID
) -> SimpleResponse:
    return await repo.delete_post(post_uuid=post_uuid, profile_uuid=profile_uuid)


async def update_post_usecase(
    repo: PostRepo, body: schemas.PostUpdate
) -> schemas.PostOut:
    return await repo.update_post(body=body)


async def list_post_for_given_profile_usecase(
    repo: PostRepo, profile_uuid: UUID, limit: int = 100, offset: int = 0
) -> PaginatedResponse[schemas.PostOut]:
    return await repo.list_posts_for_given_profile(
        profile_uuid=profile_uuid, limit=limit, offset=offset
    )


async def list_others_post_usecase(
    repo: PostRepo, profile_uuid: UUID, viewer_profile_uuid: UUID
) -> list[schemas.PostOut]:
    return await repo.list_others_posts(
        profile_uuid=profile_uuid, viewer_profile_uuid=viewer_profile_uuid
    )


async def upsert_post_position_metadata_usecase(
    repo: PostRepo, body: schemas.PostPositionMetadata
) -> schemas.PostPositionMetadata:
    return await repo.upsert_post_position_metadata(body=body)


async def get_layout_usecase(
    repo: PostRepo, profile_uuid: UUID
) -> schemas.PostPositionMetadata:
    return await repo.get_layout(profile_uuid=profile_uuid)


async def view_post_usecase(
    repo: PostRepo,
    logged_in_profile_uuid: UUID,
    viewer_uuid: UUID,
    post_uuid: UUID,
):
    return await repo.view_post(
        logged_in_profile_uuid=logged_in_profile_uuid,
        viewer_uuid=viewer_uuid,
        post_uuid=post_uuid,
    )


async def get_post_metadata_usecase(
    repo: PostRepo,
    post_uuid: UUID,
    logged_in_profile_uuid: UUID,
    viewer_uuid: UUID,
):
    return await repo.get_metadata(
        post_uuid=post_uuid,
        logged_in_profile_uuid=logged_in_profile_uuid,
        viewer_uuid=viewer_uuid,
    )


async def get_post_by_uuid_usecase(repo: PostRepo, post_uuid: UUID) -> schemas.PostOut:
    return await repo.get_post_by_uuid(post_uuid=post_uuid)


async def like_unlike_post_usecase(
    repo: PostRepo,
    logged_in_profile_uuid: UUID,
    liker_uuid: UUID,
    post_uuid: UUID,
):
    return await repo.like_unlike_post(
        logged_in_profile_uuid=logged_in_profile_uuid,
        liker_uuid=liker_uuid,
        post_uuid=post_uuid,
    )


async def search_post_usecase(
    repo: PostRepo,
    searcher_uuid: UUID,
    title: str,
    keywords: str,
    genre: core_schemas.HashTag | None,
    limit: int,
    offset: int,
):
    return await repo.search_post(
        searcher_uuid=searcher_uuid,
        title=title,
        keywords=keywords,
        genre=genre,
        limit=limit,
        offset=offset,
    )


async def search_all_usecase(
    repo: PostRepo,
    searcher_uuid: UUID,
    keywords: str,
):
    return await repo.search_all(searcher_uuid=searcher_uuid, keyword=keywords)


async def get_all_post_usecase(
    repo: PostRepo, profile_uuid: UUID
) -> list[schemas.PostOut]:
    return await repo.get_all_self_post(profile_uuid=profile_uuid)
