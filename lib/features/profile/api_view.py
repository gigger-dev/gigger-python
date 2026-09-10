import datetime
from typing import List
from uuid import UUID

from core.cvb import cbv
from core.dependencies import get_db_session
from core.global_import import AsyncSession
from core.permissions import get_current_user, is_verified_user
from core.response import PaginatedResponse, SimpleResponse
from fastapi import APIRouter, Depends, Query
from features.accounts import models
from features.profile import schemas
from features.profile.controller import FollowerController, ProfileController

profile_router = APIRouter(prefix="/api/v1/profiles", tags=["Profiles"])
follower_tag = "Follower"


@cbv(profile_router)
class ProfileAPIView:
    def __init__(
        self,
        db_session: AsyncSession = Depends(get_db_session),
        account: models.Account = Depends(get_current_user),
    ) -> None:
        self.db_session = db_session
        self.account = account
        self.controller: ProfileController = ProfileController(db_session=db_session)
        self.follower_controller: FollowerController = FollowerController(
            db_session=db_session
        )

    @profile_router.get("/interests")
    async def list_interests(
        self, query: str | None = None
    ) -> list[schemas.InterestOut]:
        return await self.controller.list_interests(query=query or "")

    @profile_router.get("/services")
    async def list_services(
        self, query: str | None = None
    ) -> list[schemas.MyServicesOut]:
        return await self.controller.list_services(query=query or "")

    @profile_router.get("/skills")
    async def list_skills(self, query: str | None = None) -> list[schemas.SkillOut]:
        return await self.controller.list_skills(query=query or "")

    @profile_router.get("/", response_model=schemas.ProfileOut)
    async def get_profile(
        self,
        account_uuid: UUID,
        account: models.Account = Depends(is_verified_user),
    ) -> schemas.ProfileOut:
        return await self.controller.get_profile(account_uuid=self.account.uuid)

    @profile_router.post(
        "/",
        response_model=schemas.ProfileOut,
    )
    async def create_profile(
        self,
        body: schemas.ProfileIn,
        _: models.Account = Depends(is_verified_user),
    ) -> schemas.ProfileOut:
        return await self.controller.create_profile(body=body)

    @profile_router.patch("/{profile_uuid}", response_model=schemas.ProfileOut)
    async def update_profile(
        self,
        profile_uuid: UUID,
        body: schemas.ProfileUpdate,
        _: models.Account = Depends(is_verified_user),
    ) -> schemas.ProfileOut:
        return await self.controller.update_profile(
            body=body, profile_uuid=profile_uuid
        )

    @profile_router.get(
        "/{profile_uuid}/recommended-artist/",
        response_model=PaginatedResponse[schemas.ProfileOut],
    )
    async def list_profiles_for_given_profile(
        self,
        profile_uuid: UUID,
        limit: int = Query(
            100, ge=1, le=1000, description="Number of items to fetch (1-1000)"
        ),
        offset: int = Query(0, ge=0, description="Number of items to skip (0 or more)"),
        _: models.Account = Depends(is_verified_user),
    ) -> PaginatedResponse[schemas.ProfileOut]:
        assert self.account.profile.uuid == profile_uuid, (
            "Each profile can only see its own recommended artists."
        )
        return await self.controller.list_profiles_for_given_profile(
            profile_uuid=self.account.profile.uuid, limit=limit, offset=offset
        )

    @profile_router.get(
        "/{profile_uuid}/",
        response_model=schemas.ProfileOut,
    )
    async def get_others_profile(
        self,
        profile_uuid: UUID,
        _: models.Account = Depends(is_verified_user),
    ) -> schemas.ProfileOut:
        return await self.controller.get_others_profile(profile_uuid=profile_uuid)

    # get metadata
    @profile_router.get(
        "/{profile_uuid}/metadata/", response_model=schemas.ProfileMetaDataOut
    )
    async def get_metadata(
        self,
        profile_uuid: UUID,
        account: models.Account = Depends(is_verified_user),
    ) -> schemas.ProfileMetaDataOut:
        return await self.controller.get_metadata(
            profile_uuid=profile_uuid, self_uuid=account.profile.uuid
        )

    @profile_router.get(
        "/{profile_uuid}/followers/",
        response_model=PaginatedResponse[schemas.ProfileFewerDetailsOut],
    )
    async def list_my_followers(
        self,
        profile_uuid: UUID,
        limit: int = Query(
            100, ge=1, le=1000, description="Number of items to fetch (1-1000)"
        ),
        offset: int = Query(0, ge=0, description="Number of items to skip (0 or more)"),
        _: models.Account = Depends(is_verified_user),
    ) -> PaginatedResponse[schemas.ProfileFewerDetailsOut]:
        return await self.follower_controller.list_my_followers(
            profile_uuid=profile_uuid, limit=limit, offset=offset
        )

    @profile_router.get(
        "/{profile_uuid}/followers/search/",
        response_model=List[schemas.ProfileFewerDetailsOut],
    )
    async def search_my_followers(
        self,
        profile_uuid: UUID,
        username: str,
        _: models.Account = Depends(is_verified_user),
    ) -> List[schemas.ProfileFewerDetailsOut]:
        return await self.follower_controller.search_my_follower(
            profile_uuid=profile_uuid,
            username=username,
        )

    @profile_router.get(
        "/{profile_uuid}/following/",
        response_model=PaginatedResponse[schemas.ProfileFewerDetailsOut],
    )
    async def list_my_following(
        self,
        profile_uuid: UUID,
        limit: int = Query(
            100, ge=1, le=1000, description="Number of items to fetch (1-1000)"
        ),
        offset: int = Query(0, ge=0, description="Number of items to skip (0 or more)"),
        _: models.Account = Depends(is_verified_user),
    ) -> PaginatedResponse[schemas.ProfileFewerDetailsOut]:
        return await self.follower_controller.list_my_following(
            profile_uuid=profile_uuid, limit=limit, offset=offset
        )

    # @profile_router.get(
    #     "/{profile_uuid}/follow/requests/",
    #     response_model=PaginatedResponse[schemas.ProfileFewerDetailsOut],
    # )
    # async def list_pending_requests(
    #     self,
    #     profile_uuid: UUID,
    #     limit: int = Query(
    #         100, ge=1, le=1000, description="Number of items to fetch (1-1000)"
    #     ),
    #     offset: int = Query(0, ge=0, description="Number of items to skip (0 or more)"),
    #     _: models.Account = Depends(is_verified_user),
    # ) -> PaginatedResponse[schemas.ProfileFewerDetailsOut]:
    #     return await self.controller.list_pending_requests(
    #         profile_uuid=self.account.profile.uuid, limit=limit, offset=offset
    #     )

    @profile_router.post(
        "/{profile_uuid}/follow-another-profile/",
        response_model=SimpleResponse,
        tags=[follower_tag],
    )
    async def request_to_follow_profile(
        self,
        profile_uuid: UUID,
        profile_to_follow: UUID,
        account: models.Account = Depends(is_verified_user),
    ) -> SimpleResponse:
        assert self.account.profile.uuid == profile_uuid, "Invalid profile_uuid"
        return await self.follower_controller.follow_another_profile(
            profile_to_follow=profile_to_follow, follower_uuid=account.profile.uuid
        )

    @profile_router.delete(
        "/{profile_uuid}/unfollow-another-profile/",
        response_model=SimpleResponse,
        tags=[follower_tag],
    )
    async def unfollow_another_profile(
        self,
        profile_to_unfollow: UUID,
        profile_uuid: UUID,
        account: models.Account = Depends(is_verified_user),
    ) -> SimpleResponse:
        assert self.account.profile.uuid == profile_uuid, "Invalid profile_uuid"
        return await self.follower_controller.unfollow_another_profile(
            profile_to_unfollow=profile_to_unfollow, follower_uuid=account.profile.uuid
        )

    @profile_router.delete(
        "/{profile_uuid}/remove-my-follower/",
        response_model=SimpleResponse,
        tags=[follower_tag],
    )
    async def remove_my_follower(
        self,
        profile_to_remove: UUID,
        profile_uuid: UUID,
        account: models.Account = Depends(is_verified_user),
    ) -> SimpleResponse:
        assert self.account.profile.uuid == profile_uuid, "Invalid profile_uuid"
        return await self.follower_controller.remove_my_follower(
            profile_to_remove=profile_to_remove, self_profile=account.profile.uuid
        )

    @profile_router.post(
        "/{profile_uuid}/request-to-follow-private-profile/",
        response_model=SimpleResponse,
    )
    async def request_to_follow_a_private_profile(
        self,
        profile_uuid: UUID,
        profile_to_request_to_follow: UUID,
        _: models.Account = Depends(is_verified_user),
    ) -> SimpleResponse:
        return await self.follower_controller.request_to_follow_for_private_profile(
            profile_to_request_to_follow=profile_to_request_to_follow,
            follower_requester_uuid=self.account.profile.uuid,
        )

    @profile_router.post(
        "/{profile_uuid}/accept-or-reject-follow-request/",
        response_model=SimpleResponse,
    )
    async def accept_or_reject_follow_request_to_private_profile(
        self,
        profile_uuid: UUID,
        profile_to_accept_or_reject: UUID,
        is_accepted: bool,
        _: models.Account = Depends(is_verified_user),
    ) -> SimpleResponse:
        assert self.account.profile.uuid == profile_uuid, "Invalid profile_uuid"
        return await self.follower_controller.accept_or_reject_request_to_follow_for_private_profile(
            profile_to_accept_or_reject=profile_to_accept_or_reject,
            follower_accepter_or_rejecter_uuid=self.account.profile.uuid,
            is_accepted=is_accepted,
        )

    @profile_router.post("/{canceler}/cancel-request-to-follow/")
    async def cancel_request_to_follow_for_private_profile(
        self, canceler: UUID, profile_to_cancel_follow_request: UUID
    ):
        return (
            await self.follower_controller.cancel_request_to_follow_for_private_profile(
                canceler=self.account.profile.uuid,
                profile_to_cancel_follow_request=profile_to_cancel_follow_request,
            )
        )

    @profile_router.post(
        "/{profile_uuid}/toggle-private-profile-mode/",
        response_model=schemas.ProfileOut,
    )
    async def toggle_private_profile_model(
        self,
        is_private: bool,
        profile_uuid: UUID,
        _: models.Account = Depends(is_verified_user),
    ):
        assert self.account.profile.uuid == profile_uuid
        return await self.controller.toggle_private_profile_mode(
            profile_uuid=self.account.profile.uuid, is_private=is_private
        )

    @profile_router.post(
        "/{profile_uuid}/view/", response_model=schemas.ProfileMetaDataOut
    )
    async def view_profile(
        self,
        viewer_uuid: UUID,
        profile_uuid: UUID,
    ):
        return await self.controller.view_profile(
            viewer_uuid=viewer_uuid,
            profile_uuid=profile_uuid,
        )

    @profile_router.get(
        "/{profile_uuid}/search/",
        response_model=PaginatedResponse[schemas.ProfileOut],
    )
    async def search_profile(
        self,
        profile_uuid: UUID,
        username: str | None = Query(None),
        role: str | None = Query(None),
        genre: str | None = Query(None),
        instrument: str | None = Query(None),
        start_date: datetime.datetime | None = Query(None),
        end_date: datetime.datetime | None = Query(None),
        limit: int = 50,
        offset: int = 0,
        pro_user_only: bool = False,
    ):
        assert profile_uuid == self.account.profile.uuid, "Invalid profile uuid"
        return await self.controller.search_profile(
            searcher_uuid=self.account.profile.uuid,
            username=username,
            role=role,
            genre=genre,
            instrument=instrument,
            availability=schemas.AvailabilitySearchParam(
                start_date=start_date, end_date=end_date
            )
            if start_date and end_date
            else None,
            limit=limit,
            offset=offset,
            pro_user_only=pro_user_only,
        )
