from uuid import UUID

from core.global_import import AsyncSession
from core.response import PaginatedResponse, SimpleResponse
from features.profile import schemas
from features.profile.repo import NewFollowerRepoImpl, ProfileRepoImpl
from features.profile.usecase import (
    accept_or_reject_request_to_follow_for_private_profile_usecase,
    cancel_request_to_follow_for_private_profile_usecase,
    create_profile_usecase,
    follow_another_profile_usecase,
    get_others_profile_usecase,
    get_profile_metadata_usecase,
    get_profile_usecase,
    list_interests_usecase,
    list_my_follower_usecase,
    list_my_following_usecase,
    list_profiles_for_given_profile_usecase,
    list_services_usecase,
    list_skills_usecase,
    remove_my_follower_usecase,
    request_to_follow_for_private_profile_usecase,
    search_my_follower_usecase,
    search_profile_usecase,
    toggle_private_profile_mode,
    unfollow_another_profile_usecase,
    update_profile_usecase,
    view_profile_usecase,
)


class ProfileController:
    def __init__(self, db_session: AsyncSession) -> None:
        self.repo = ProfileRepoImpl(db_session=db_session)

    async def list_interests(self, query: str) -> list[schemas.InterestOut]:
        return await list_interests_usecase(repo=self.repo, query=query)

    async def list_services(self, query: str) -> list[schemas.MyServicesOut]:
        return await list_services_usecase(repo=self.repo, query=query)

    async def list_skills(self, query: str) -> list[schemas.SkillOut]:
        return await list_skills_usecase(repo=self.repo, query=query)

    async def create_profile(self, body: schemas.ProfileIn) -> schemas.ProfileOut:
        return await create_profile_usecase(repo=self.repo, body=body)

    async def get_profile(self, account_uuid: UUID) -> schemas.ProfileOut:
        return await get_profile_usecase(repo=self.repo, account_uuid=account_uuid)

    async def update_profile(
        self, profile_uuid: UUID, body: schemas.ProfileUpdate
    ) -> schemas.ProfileOut:
        return await update_profile_usecase(
            repo=self.repo, profile_uuid=profile_uuid, body=body
        )

    async def list_profiles_for_given_profile(
        self, profile_uuid: UUID, limit: int = 100, offset: int = 0
    ) -> PaginatedResponse[schemas.ProfileOut]:
        return await list_profiles_for_given_profile_usecase(
            repo=self.repo, profile_uuid=profile_uuid, limit=limit, offset=offset
        )

    async def get_others_profile(self, profile_uuid: UUID) -> schemas.ProfileOut:
        return await get_others_profile_usecase(
            repo=self.repo, profile_uuid=profile_uuid
        )

    async def get_metadata(
        self, profile_uuid: UUID, self_uuid: UUID
    ) -> schemas.ProfileMetaDataOut:
        return await get_profile_metadata_usecase(
            repo=self.repo, profile_uuid=profile_uuid, self_uuid=self_uuid
        )

    async def toggle_private_profile_mode(self, profile_uuid: UUID, is_private: bool):
        return await toggle_private_profile_mode(
            repo=self.repo, profile_uuid=profile_uuid, is_private=is_private
        )

    async def view_profile(
        self,
        viewer_uuid: UUID,
        profile_uuid: UUID,
    ):
        return await view_profile_usecase(
            repo=self.repo,
            viewer_uuid=viewer_uuid,
            profile_uuid=profile_uuid,
        )

    async def search_profile(
        self,
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
        return await search_profile_usecase(
            repo=self.repo,
            searcher_uuid=searcher_uuid,
            username=username,
            role=role,
            genre=genre,
            availability=availability,
            limit=limit,
            offset=offset,
            pro_user_only=pro_user_only,
            instrument=instrument,
        )


class FollowerController:
    def __init__(self, db_session: AsyncSession) -> None:
        self.follower_repo = NewFollowerRepoImpl(db_session=db_session)

    async def list_my_followers(
        self, profile_uuid: UUID, limit: int = 100, offset: int = 0
    ) -> PaginatedResponse[schemas.ProfileFewerDetailsOut]:
        return await list_my_follower_usecase(
            repo=self.follower_repo,
            profile_uuid=profile_uuid,
            limit=limit,
            offset=offset,
        )

    async def list_my_following(
        self, profile_uuid: UUID, limit: int = 100, offset: int = 0
    ) -> PaginatedResponse[schemas.ProfileFewerDetailsOut]:
        return await list_my_following_usecase(
            repo=self.follower_repo,
            profile_uuid=profile_uuid,
            limit=limit,
            offset=offset,
        )

    async def follow_another_profile(
        self, profile_to_follow: UUID, follower_uuid: UUID
    ) -> SimpleResponse:
        return await follow_another_profile_usecase(
            repo=self.follower_repo,
            profile_to_follow=profile_to_follow,
            follower_uuid=follower_uuid,
        )

    async def unfollow_another_profile(
        self, profile_to_unfollow: UUID, follower_uuid: UUID
    ):
        return await unfollow_another_profile_usecase(
            repo=self.follower_repo,
            profile_to_unfollow=profile_to_unfollow,
            follower_uuid=follower_uuid,
        )

    async def remove_my_follower(self, profile_to_remove: UUID, self_profile: UUID):
        return await remove_my_follower_usecase(
            repo=self.follower_repo,
            profile_to_remove=profile_to_remove,
            self_profile=self_profile,
        )

    async def request_to_follow_for_private_profile(
        self, profile_to_request_to_follow: UUID, follower_requester_uuid: UUID
    ):
        return await request_to_follow_for_private_profile_usecase(
            repo=self.follower_repo,
            profile_to_request_to_follow=profile_to_request_to_follow,
            follower_requester_uuid=follower_requester_uuid,
        )

    async def accept_or_reject_request_to_follow_for_private_profile(
        self,
        profile_to_accept_or_reject: UUID,
        follower_accepter_or_rejecter_uuid: UUID,
        is_accepted: bool,
    ):
        return await accept_or_reject_request_to_follow_for_private_profile_usecase(
            repo=self.follower_repo,
            profile_to_accept_or_reject=profile_to_accept_or_reject,
            follower_accepter_or_rejecter_uuid=follower_accepter_or_rejecter_uuid,
            is_accepted=is_accepted,
        )

    async def cancel_request_to_follow_for_private_profile(
        self, canceler: UUID, profile_to_cancel_follow_request: UUID
    ):
        return await cancel_request_to_follow_for_private_profile_usecase(
            repo=self.follower_repo,
            canceler=canceler,
            profile_to_cancel_follow_request=profile_to_cancel_follow_request,
        )

    async def search_my_follower(
        self,
        profile_uuid: UUID,
        username: str,
    ):
        return await search_my_follower_usecase(
            repo=self.follower_repo,
            profile_uuid=profile_uuid,
            username=username,
        )
