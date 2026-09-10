from uuid import UUID

from core.global_import import AsyncSession
from core.response import BasicResponse
from features.settings.repo import SettingRepoImpl
from features.settings.schemas import DeviceTokenIn
from features.settings.usecase import (
    create_device_token_usecase,
    delete_notification_usecase,
    get_notifications_usecase,
    get_stream_chat_token_usecase,
    logout_usecase,
)


class DeviceTokenController:
    def __init__(self, db_session: AsyncSession):
        self.repo = SettingRepoImpl(db_session=db_session)

    async def create_device_token(self, body: DeviceTokenIn):
        return await create_device_token_usecase(repo=self.repo, body=body)

    async def logout(self, profile_uuid: UUID, device_uuid: str) -> BasicResponse:
        return await logout_usecase(
            repo=self.repo, profile_uuid=profile_uuid, device_uuid=device_uuid
        )

    async def get_notifications(self, profile_uuid: UUID):
        return await get_notifications_usecase(
            repo=self.repo, profile_uuid=profile_uuid
        )

    async def get_stream_chat_token(self, user_uuid: UUID) -> str:
        return await get_stream_chat_token_usecase(repo=self.repo, user_uuid=user_uuid)

    async def delete_notification(self, notification_uuid: int):
        return await delete_notification_usecase(
            repo=self.repo, notification_uuid=notification_uuid
        )
