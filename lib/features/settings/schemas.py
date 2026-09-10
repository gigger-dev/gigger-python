from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ServerConfigOut(BaseModel):
    base_url: str
    cdn_url: str


class DeviceTokenIn(BaseModel):
    fcm_token: str
    device_uuid: str
    profile_uuid: UUID


class NotificationIn(BaseModel):
    title: str
    body: str
    data: dict[str, Any]
    notification_type: int
    profile_uuid: UUID


class NotificationOut(NotificationIn):
    created_at: datetime
    updated_at: datetime
    id: int


class NotificationDataType(Enum):
    PROFILE = 0
    POST = 1
    GIG_LIST = 2
    SUP = 3
    EVENT = 4
    PRO_SERVICES = 5
    CAMPAIGNS = 6


class NotificationType(Enum):
    REQUEST_ACCEPTED = 0
    NEW_FOLLOWER = 1
    NEW_MESSAGE = 2
    NEW_POST = 3
    NEW_LIKE = 4
    NEW_COMMENT = 5
    NEW_SHARE = 6
    NEW_SUBSCRIPTION = 7
    NEW_EVENT = 8
    NEW_PRO_SERVICE = 9
    NEW_FOLLOW_REQUEST = 10
    NEW_VIEW = 11

    NEW_REQUEST = 12
    REQUEST_REJECTED = 13  # eg. event invite rejection.
    NEW_MENTION = 14

    def get_notification_body(self, name: str, type: NotificationDataType):
        """_summary_

        Args:
            name (str): name that does the action not the notification receiver.
            type (NotificationDataType): data type of notification
        """
        text = ""
        if self.value == 0:
            text = f"{name} has accepted your {type.name.lower()} request."
        if self.value == 1:
            text = f"{name} has followed you."
        if self.value == 2:
            text = f"{name} sent you a message."
        if self.value == 3:
            text = f"{name} shared a new post."
        if self.value == 4:
            text = f"{name} liked your {type.name.lower()}."
        if self.value == 5:
            text = f"{name} commented on your {type.name.lower()}."
        if self.value == 6:
            text = f"{name} shared your {type.name.lower()}."
        if self.value == 7:
            text = f"{name} Subscribed to your services."
        if self.value == 8:
            text = f"{name} hosted an event."
        if self.value == 9:
            text = f"{name} has a new {type.name.lower()}."
        if self.value == 10:
            text = f"{name} sent a request to follow you."
        if self.value == 11:
            text = f"{name} has viewed your {type.name.lower()}."
        if self.value == 12:
            text = f"You have received an event invitation from {name}."
        if self.value == 13:
            text = f"{name} has rejected your {type.name.lower()} request."
        if self.value == 14:
            text = f"{name} mention you in a post."
        return text


class NotificationBodySchema(BaseModel):
    model_config = ConfigDict(use_enum_values=True)
    notification_type: int
    profile_uuid: str
    profile_name: str
    profile_image: str
    uuid: str
    """
    The uuid of POST,GIG_LIST,SUP etc.
    """
    notification_data_type: int | None = None
