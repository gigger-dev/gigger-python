from typing import Any, List
from uuid import UUID

import sqlalchemy as sa
from core.config import settings
from core.db_model_utils import Base, DateMixin, IDMixin, ModelManager
from core.push_notification_service import send_multicast_notification
from fastapi.logger import logger
from features.profile.models import ProfileFKMixin
from features.settings import schemas
from features.settings.schemas import (
    DeviceTokenIn,
    NotificationBodySchema,
    NotificationDataType,
    NotificationIn,
    NotificationOut,
    NotificationType,
)
from pydantic import BaseModel
from sqlalchemy import UniqueConstraint
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column


class ServerConfig(
    Base,
    IDMixin,
    DateMixin,
):
    __tablename__ = "gigger_server_config"
    cdn_url = sa.Column(sa.String(256), nullable=True)
    base_url = sa.Column(sa.String(256), nullable=True)

    def __repr__(self):
        return f"<ServerConfig(id={self.id}, base_url={self.base_url}, cdn_url={self.cdn_url})>"

    def to_pydantic(self) -> BaseModel:
        return schemas.ServerConfigOut.model_validate(self, from_attributes=True)


class DeviceToken(Base, DateMixin, ProfileFKMixin, IDMixin, ModelManager):
    """
    Device token model for storing device token.
    # Logout လုပ်လျှင် device id and profile_uuid အပေါ်မူတည်ပီး Token ပြန်ဖြစ်ပေးရမယ်
    # notification ပို့တဲ့အခါ့ Login ၀င်ထားတဲ့ device အားလုံးကို profile UUID နဲ့ခေါ်ပီး ပို့ပေးရမယ်
    #
    """

    __tablename__ = "gigger_device_tokens"

    fcm_token: Mapped[str]
    device_uuid: Mapped[str]
    __table_args__ = (
        UniqueConstraint(
            "device_uuid",
            "profile_uuid",
            name="unique_fcm_token_device_uuid",
        ),
    )

    def to_pydantic(self) -> DeviceTokenIn:
        return DeviceTokenIn(
            fcm_token=self.fcm_token,
            device_uuid=self.device_uuid,
            profile_uuid=self.profile_uuid,
        )


class Notification(Base, IDMixin, ProfileFKMixin, DateMixin, ModelManager):
    __tablename__ = "gigger_notifications"
    title: Mapped[str]
    body: Mapped[str]
    data: Mapped[dict[str, Any]]
    notification_type: Mapped[int] = mapped_column(
        sa.SmallInteger, default=0
    )  # I don't know how many notification type so just int for type.

    def to_pydantic(self) -> NotificationOut:
        return NotificationOut.model_validate(self, from_attributes=True)

    def __repr__(self):
        return f"<Notification(id={self.id}, title={self.title}, body={self.body}, data={self.data}, type={self.notification_type})>"

    async def send_multicast_notification(
        self,
        profile_uuid_to_send_notification: UUID,
        db_session: AsyncSession,
    ):
        device_tokens = await DeviceToken.list(
            db_session=db_session,
            profile_uuid=profile_uuid_to_send_notification,
        )
        if not device_tokens:
            return
        fcm_tokens = [device_token.fcm_token for device_token in device_tokens]
        await send_multicast_notification(
            device_tokens=fcm_tokens,
            title=self.title,
            body=self.body,
            data={key: str(value) for key, value in self.data.items()},
        )

    @classmethod
    async def setup_and_send_notifications(
        cls,
        profile_uuid_to_send_notification: List[UUID],
        db_session: AsyncSession,
        notification_body: NotificationBodySchema,
        notification_data_type: NotificationDataType,
    ):
        if profile_uuid_to_send_notification == notification_body.profile_uuid:
            return
        type = NotificationType(notification_body.notification_type)
        notification_ins: List[NotificationIn] = []
        for profile_uuid in profile_uuid_to_send_notification:
            notification_in = NotificationIn(
                title=type.name,
                body=type.get_notification_body(
                    name=notification_body.profile_name,
                    type=notification_data_type,
                ),
                data=notification_body.model_dump(),
                notification_type=notification_body.notification_type,
                profile_uuid=profile_uuid,
            )
            notification_ins.append(notification_in)
        if notification_ins:
            stmt = sa.insert(Notification).values(
                [n.model_dump() for n in notification_ins]
            )
            await db_session.execute(stmt)
            await db_session.commit()

        if notification_ins and not settings.debug:
            stmt = sa.select(DeviceToken).where(
                DeviceToken.profile_uuid.in_(profile_uuid_to_send_notification),
            )
            device_tokens = await db_session.scalars(stmt)
            fcm_tokens = [device_token.fcm_token for device_token in device_tokens]
            try:
                await send_multicast_notification(
                    device_tokens=fcm_tokens,
                    title=type.name,
                    body=type.get_notification_body(
                        name=notification_body.profile_name,
                        type=notification_data_type,
                    ),
                    data={
                        key: str(value)
                        for key, value in notification_body.model_dump().items()
                    },
                )
            except Exception as e:
                logger.error(e)
                pass
