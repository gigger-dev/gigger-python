from typing import List
from uuid import UUID

from core.response import PaginatedResponse, SimpleResponse
from features.profile import schemas
from features.profile.repo import NewFollowerRepo, ProfileRepo


async def list_interests_usecase(
    repo: ProfileRepo, query: str
) -> list[schemas.InterestOut]:
    return await repo.list_interests(query=query)


async def list_services_usecase(
    repo: ProfileRepo, query: str
) -> list[schemas.MyServicesOut]:
    return await repo.list_services(query=query)


async def list_skills_usecase(repo: ProfileRepo, query: str) -> list[schemas.SkillOut]:
    return await repo.list_skills(query=query)


async def create_profile_usecase(
    repo: ProfileRepo, body: schemas.ProfileIn
) -> schemas.ProfileOut:
    return await repo.create_profile(body=body)


async def get_profile_usecase(
    repo: ProfileRepo, account_uuid: UUID
) -> schemas.ProfileOut:
    return await repo.get_profile(account_uuid=account_uuid)


async def update_profile_usecase(
    repo: ProfileRepo, profile_uuid: UUID, body: schemas.ProfileUpdate
) -> schemas.ProfileOut:
    return await repo.update_profile(profile_uuid=profile_uuid, body=body)


async def list_profiles_for_given_profile_usecase(
    repo: ProfileRepo, profile_uuid: UUID, limit: int = 100, offset: int = 0
) -> PaginatedResponse[schemas.ProfileOut]:
    return await repo.list_profiles_for_given_profile(
        profile_uuid=profile_uuid, limit=limit, offset=offset
    )


async def get_others_profile_usecase(
    repo: ProfileRepo, profile_uuid: UUID
) -> schemas.ProfileOut:
    return await repo.get_others_profile(profile_uuid=profile_uuid)


async def get_profile_metadata_usecase(
    repo: ProfileRepo, profile_uuid: UUID, self_uuid: UUID
) -> schemas.ProfileMetaDataOut:
    return await repo.get_metadata(profile_uuid=profile_uuid, self_uuid=self_uuid)


async def toggle_private_profile_mode(
    repo: ProfileRepo, profile_uuid: UUID, is_private: bool
) -> schemas.ProfileOut:
    return await repo.toggle_private_mode(
        profile_uuid=profile_uuid, is_private=is_private
    )


async def list_my_follower_usecase(
    repo: NewFollowerRepo, profile_uuid: UUID, limit: int = 100, offset: int = 0
) -> PaginatedResponse[schemas.ProfileFewerDetailsOut]:
    return await repo.list_my_follower(
        profile_uuid=profile_uuid, limit=limit, offset=offset
    )


async def search_my_follower_usecase(
    repo: NewFollowerRepo, profile_uuid: UUID, username: str
) -> List[schemas.ProfileFewerDetailsOut]:
    return await repo.search_my_follower(
        profile_uuid=profile_uuid,
        username=username,
    )


async def list_my_following_usecase(
    repo: NewFollowerRepo, profile_uuid: UUID, limit: int = 100, offset: int = 0
) -> PaginatedResponse[schemas.ProfileFewerDetailsOut]:
    return await repo.list_my_following(
        profile_uuid=profile_uuid, limit=limit, offset=offset
    )


async def follow_another_profile_usecase(
    repo: NewFollowerRepo, profile_to_follow: UUID, follower_uuid: UUID
) -> SimpleResponse:
    return await repo.follow_another_profile(
        profile_to_follow=profile_to_follow, follower_uuid=follower_uuid
    )


async def unfollow_another_profile_usecase(
    repo: NewFollowerRepo, profile_to_unfollow: UUID, follower_uuid: UUID
) -> SimpleResponse:
    return await repo.unfollow_another_profile(
        profile_to_unfollow=profile_to_unfollow, follower_uuid=follower_uuid
    )


async def remove_my_follower_usecase(
    repo: NewFollowerRepo, profile_to_remove: UUID, self_profile: UUID
) -> SimpleResponse:
    return await repo.remove_my_follower(
        profile_to_remove=profile_to_remove, self_profile=self_profile
    )


async def request_to_follow_for_private_profile_usecase(
    repo: NewFollowerRepo,
    profile_to_request_to_follow: UUID,
    follower_requester_uuid: UUID,
) -> SimpleResponse:
    return await repo.request_to_follow_for_private_profile(
        profile_to_request_to_follow=profile_to_request_to_follow,
        follower_requester_uuid=follower_requester_uuid,
    )


async def accept_or_reject_request_to_follow_for_private_profile_usecase(
    repo: NewFollowerRepo,
    profile_to_accept_or_reject: UUID,
    follower_accepter_or_rejecter_uuid: UUID,
    is_accepted: bool,
) -> SimpleResponse:
    return await repo.accept_or_reject_request_to_follow_for_private_profile(
        profile_to_accept_or_reject=profile_to_accept_or_reject,
        follower_accepter_or_rejecter_uuid=follower_accepter_or_rejecter_uuid,
        is_accepted=is_accepted,
    )


async def cancel_request_to_follow_for_private_profile_usecase(
    repo: NewFollowerRepo, canceler: UUID, profile_to_cancel_follow_request: UUID
):
    return await repo.cancel_request_to_follow_for_private_profile(
        canceler=canceler,
        profile_to_cancel_follow_request=profile_to_cancel_follow_request,
    )


async def view_profile_usecase(
    repo: ProfileRepo,
    viewer_uuid: UUID,
    profile_uuid: UUID,
):
    return await repo.view_profile(
        viewer_uuid=viewer_uuid,
        profile_uuid=profile_uuid,
    )


async def search_profile_usecase(
    repo: ProfileRepo,
    searcher_uuid: UUID,
    username: str | None,
    role: str | None,
    genre: str | None,
    instrument: str | None,
    availability: schemas.AvailabilitySearchParam | None,
    limit: int = 50,
    offset: int = 0,
    pro_user_only: bool = False,
):
    return await repo.search_profile(
        searcher_uuid=searcher_uuid,
        username=username,
        role=role,
        genre=genre,
        instrument=instrument,
        availability=availability,
        limit=limit,
        offset=offset,
        pro_user_only=pro_user_only,
    )
