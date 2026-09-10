from abc import ABC, abstractmethod
from uuid import UUID

from core.dependencies import stream_chat_server_client
from core.global_import import AsyncSession
from core.response import BasicResponse
from fastapi import HTTPException
from features.settings.models import DeviceToken, Notification
from features.settings.schemas import DeviceTokenIn, NotificationOut
from sqlalchemy import desc


class SettingRepo(ABC):
    @abstractmethod
    async def create_or_update_device_token(self, body: DeviceTokenIn) -> DeviceTokenIn:
        pass

    @abstractmethod
    async def logout(self, profile_uuid: UUID, device_uuid: str) -> BasicResponse:
        pass

    @abstractmethod
    async def get_notifications(self, profile_uuid: UUID) -> list[NotificationOut]:
        pass

    @abstractmethod
    async def delete_notification(self, notification_uuid: int) -> BasicResponse:
        pass

    @abstractmethod
    async def get_stream_chat_token(self, user_uuid: UUID) -> str:
        pass


class SettingRepoImpl(SettingRepo):
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_or_update_device_token(self, body: DeviceTokenIn):
        stmt = None
        if self.db_session.bind.dialect.name == "postgresql":
            import sqlalchemy.dialects.postgresql as pa

            stmt = (
                pa.insert(DeviceToken)
                .values(
                    fcm_token=body.fcm_token,
                    device_uuid=body.device_uuid,
                    profile_uuid=body.profile_uuid,
                )
                .on_conflict_do_update(
                    index_elements=["device_uuid", "profile_uuid"],
                    set_={"fcm_token": body.fcm_token},
                )
                .returning(DeviceToken)
            )
        elif self.db_session.bind.dialect.name == "sqlite":
            import sqlalchemy.dialects.sqlite as sa

            stmt = (
                sa.insert(DeviceToken)
                .values(
                    fcm_token=body.fcm_token,
                    device_uuid=body.device_uuid,
                    profile_uuid=body.profile_uuid,
                )
                .on_conflict_do_update(
                    index_elements=["device_uuid", "profile_uuid"],
                    set_={"fcm_token": body.fcm_token},
                )
            ).returning(DeviceToken)
        else:
            raise HTTPException(status_code=500, detail="Unsupported database dialect.")

        try:
            result = await self.db_session.execute(stmt)
            await self.db_session.commit()
            result = result.scalar()
            if not result:
                result = await DeviceToken.get(
                    db_session=self.db_session,
                    profile_uuid=body.profile_uuid,
                    device_uuid=body.device_uuid,
                )
                if result:
                    return result.to_pydantic()
                raise HTTPException(
                    status_code=500, detail="Failed to create device token!"
                )
            return result.to_pydantic()
        except Exception as e:
            await self.db_session.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"An error occurred during token creation: {str(e)}",
            )

    async def logout(self, profile_uuid: UUID, device_uuid: str) -> BasicResponse:
        try:
            token = await DeviceToken.get(
                db_session=self.db_session,
                profile_uuid=profile_uuid,
                device_uuid=device_uuid,
            )
            if not token:
                raise HTTPException(
                    status_code=404,
                    detail="No token found for the provided profile and device.",
                )

            # Delete the token
            await token.delete(
                db_session=self.db_session,
                device_uuid=device_uuid,
                profile_uuid=profile_uuid,
            )
            await self.db_session.commit()

            return BasicResponse(message="Successfully logged out.", success=True)

        except Exception as e:
            await self.db_session.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"An error occurred during logout: {str(e)}",
            )

    async def get_notifications(self, profile_uuid: UUID) -> list[NotificationOut]:
        try:
            notifications = await Notification.list(
                db_session=self.db_session,
                profile_uuid=profile_uuid,
                limit=50,
                order_by=desc(Notification.created_at),
            )
            return [notification.to_pydantic() for notification in notifications]
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"An error occurred while fetching notifications: {str(e)}",
            )

    async def get_stream_chat_token(self, user_uuid: UUID) -> str:
        try:
            assert stream_chat_server_client
            return stream_chat_server_client.create_token(
                user_id=str(user_uuid),
            )
        except Exception as e:
            raise e

    async def delete_notification(self, notification_uuid: int) -> BasicResponse:
        noti = await Notification.get(
            db_session=self.db_session,
            id=notification_uuid,
        )
        if not noti:
            raise HTTPException(status_code=404, detail="Notification not found!")

        await noti.delete(db_session=self.db_session, id=notification_uuid)
        await self.db_session.commit()
        return BasicResponse(message="Notification deleted successfully!", success=True)
