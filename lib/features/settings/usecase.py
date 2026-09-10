from uuid import UUID

from core.response import BasicResponse
from features.settings.repo import SettingRepo
from features.settings.schemas import DeviceTokenIn


async def create_device_token_usecase(repo: SettingRepo, body: DeviceTokenIn):
    return await repo.create_or_update_device_token(body)


async def logout_usecase(
    repo: SettingRepo, profile_uuid: UUID, device_uuid: str
) -> BasicResponse:
    return await repo.logout(profile_uuid, device_uuid)


async def get_notifications_usecase(repo: SettingRepo, profile_uuid: UUID):
    return await repo.get_notifications(profile_uuid)


async def get_stream_chat_token_usecase(repo: SettingRepo, user_uuid: UUID) -> str:
    return await repo.get_stream_chat_token(user_uuid=user_uuid)


async def delete_notification_usecase(
    repo: SettingRepo, notification_uuid: int
) -> BasicResponse:
    return await repo.delete_notification(
        notification_uuid=notification_uuid,
    )
