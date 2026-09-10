from typing import List
from uuid import UUID

from core.cvb import cbv
from core.dependencies import get_db_session
from core.global_import import AsyncSession
from core.permissions import is_verified_user
from core.response import PaginatedResponse, SimpleResponse
from fastapi import APIRouter, Depends, Query
from features.accounts import models as account_models
from features.profile.schemas import ProfileFewerDetailsOut
from features.sup import schemas
from features.sup.controller import SupController

sup_router = APIRouter(prefix="/api/v1/sup", tags=["S'up"])


@cbv(sup_router)
class SupAPIView:
    def __init__(
        self,
        db_session: AsyncSession = Depends(get_db_session),
        account: account_models.Account = Depends(is_verified_user),
    ) -> None:
        self.db_session = db_session
        self.account = account
        self.controller = SupController(db_session=db_session)

    @sup_router.post("/", response_model=schemas.SupOut)
    async def create_sup(self, body: schemas.SupCreate):
        return await self.controller.create_sup(body=body)

    # TODO: only for self or search by profile
    @sup_router.get("/{profile_uuid}/", response_model=List[schemas.SupOut])
    async def list_sup(
        self, profile_uuid: UUID, created_from: schemas.SupCreatedFromEnum
    ):
        """
        profile_uuidသုံးပီး သူတင်ထားတဲ့ sup တေခေါ်လို့ရမယ်။
        UI မှာဆို profile icon ထောက်ပီးနောက်တစ်ဆင့်သွားတဲ့နေရာကခေါ်ရမယ်။
        """

        return await self.controller.list_sup(
            profile_uuid=profile_uuid, created_from=created_from
        )

    @sup_router.get("/", response_model=PaginatedResponse[ProfileFewerDetailsOut])
    async def list_profile_having_sup(
        self,
        created_from: schemas.SupCreatedFromEnum = Query(
            default=schemas.SupCreatedFromEnum.NONE
        ),
        limit: int = Query(100, ge=1, le=1000),
        offset: int = Query(0, ge=0),
    ):
        """
        ခေါ်တဲ့သူရဲ့ profile အတွက် sup ရှိတဲ့ profileတွေ return ပြန်ပေးမယ်။

        """
        return await self.controller.list_profile_having_sup(
            profile_uuid=self.account.profile.uuid,
            limit=limit,
            offset=offset,
            created_from=created_from,
        )

    @sup_router.delete("/{sup_uuid}", response_model=SimpleResponse)
    async def delete_sup(self, sup_uuid: UUID):
        return await self.controller.delete_sup(
            sup_uuid=sup_uuid, profile_uuid=self.account.profile.uuid
        )

    @sup_router.post("/{sup_uuid}/like/", response_model=schemas.SupMetadata)
    async def like_unlike_sup(
        self,
        liker_uuid: UUID,
        sup_uuid: UUID,
    ):
        return await self.controller.like_unlike_sup(
            logged_in_profile_uuid=self.account.profile.uuid,
            liker_uuid=liker_uuid,
            sup_uuid=sup_uuid,
        )

    @sup_router.get("/{sup_uuid}/metadata/", response_model=schemas.SupMetadata)
    async def get_sup_metadata(
        self,
        sup_uuid: UUID,
        viewer_uuid: UUID,
    ):
        return await self.controller.get_sup_metadata(
            sup_uuid=sup_uuid,
            logged_in_profile_uuid=self.account.profile.uuid,
            viewer_uuid=viewer_uuid,
        )

    @sup_router.post("/{sup_uuid}/share/", response_model=schemas.SupMetadata)
    async def share_sup(
        self,
        sharer_uuid: UUID,
        sup_uuid: UUID,
    ):
        return await self.controller.share_sup(
            logged_in_profile_uuid=self.account.profile.uuid,
            sharer_uuid=sharer_uuid,
            sup_uuid=sup_uuid,
        )

    @sup_router.get("/{sup_uuid}/get/", response_model=schemas.SupOut)
    async def get_sup_by_uuid(self, sup_uuid: UUID):
        return await self.controller.get_sup_by_uuid(sup_uuid=sup_uuid)

    @sup_router.post("/{sup_uuid}/view/", response_model=schemas.SupMetadata)
    async def view_sup(
        self,
        viewer_uuid: UUID,
        sup_uuid: UUID,
    ):
        return await self.controller.view_sup(
            logged_in_profile_uuid=self.account.profile.uuid,
            viewer_uuid=viewer_uuid,
            sup_uuid=sup_uuid,
        )
