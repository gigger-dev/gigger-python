import asyncio
import logging
from typing import List

from fastapi.concurrency import run_in_threadpool
from firebase_admin import messaging

logger = logging.getLogger(__name__)


async def send_multicast_notification(
    device_tokens: List[str], title: str, body: str, data: dict[str, str]
):
    try:
        msg = messaging.MulticastMessage(
            notification=messaging.Notification(title=title, body=body),
            data=data,
            tokens=device_tokens,
        )
        response = await run_in_threadpool(messaging.send_each_for_multicast, msg)
        logger.info(f"sent message to {response.success_count} device(s)")
        return response
    except Exception as e:
        raise e


if __name__ == "__main__":
    print("called")
    from main import init_firebase

    init_firebase()
    asyncio.run(  # type: ignore
        send_multicast_notification(
            title="Ye Lin Aung sent you friend request",
            body="Ye Lin Aung sent you friend request",
            data={
                "type": "friend_request",
                "profile_uuid": "b3c9c4f6-3f6d-4c0c-8e8a-5e9d0a3b1d8e",
                "profile_name": "Ye Lin Aung",
                "profile_image": "https://cdn.gigger.com/profile/1.jpg",
            },
            device_tokens=[
                "cDMrpgs5TX6gmh5FzqTvc4:APA91bFydxEg083lPggCAc2uDmf0xPamZ9CBrUV08kKQ5DN06ZhGueMDlqN8zdXxrZERi0I89sieMOEy2KbaETM2CzSnX-2D2lNiMgAR-rG1w77EeJND1MQ"
            ],
        )
    )
