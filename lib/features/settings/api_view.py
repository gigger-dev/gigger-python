from uuid import UUID

from core.cvb import cbv
from core.dependencies import get_db_session
from core.global_import import AsyncSession
from core.permissions import is_verified_user
from core.response import BasicResponse
from fastapi import APIRouter, Depends
from features.accounts import models as account_models
from features.settings import schemas
from features.settings.controller import DeviceTokenController

setting_router = APIRouter(prefix="/api/v1/config", tags=["settings"])


@setting_router.get("/", response_model=schemas.ServerConfigOut)
async def get_server_config() -> schemas.ServerConfigOut:
    return schemas.ServerConfigOut(
        base_url="api.gigger.art",
        cdn_url="https://gigger.sgp1.cdn.digitaloceanspaces.com",
    )


@cbv(setting_router)
class SettingAPIView:
    def __init__(
        self,
        db_session: AsyncSession = Depends(get_db_session),
        account: account_models.Account = Depends(is_verified_user),
    ) -> None:
        self.db_session = db_session
        self.account = account
        self.controller = DeviceTokenController(db_session=db_session)

    @setting_router.post("/fcm_token/", response_model=schemas.DeviceTokenIn)
    async def create_device_token(self, body: schemas.DeviceTokenIn):
        return await self.controller.create_device_token(body)

    @setting_router.delete(
        "/logout/",
        response_model=BasicResponse,
    )
    async def logout(self, device_uuid: str):
        return await self.controller.logout(
            device_uuid=device_uuid, profile_uuid=self.account.profile.uuid
        )

    @setting_router.get("/notifications/", response_model=list[schemas.NotificationOut])
    async def get_notifications(self):
        return await self.controller.get_notifications(self.account.profile.uuid)

    @setting_router.get("/get_stream_chat_token", response_model=str)
    async def get_stream_chat_token(self, user_uuid: UUID):
        return await self.controller.get_stream_chat_token(user_uuid=user_uuid)

    @setting_router.delete("/{notification_uuid}/", response_model=BasicResponse)
    async def delete_notification(self, notification_uuid: int):
        return await self.controller.delete_notification(notification_uuid)
