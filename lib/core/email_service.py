import logging
from abc import ABC, abstractmethod
from asyncio import get_running_loop  # type: ignore

from pydantic import EmailStr
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from core.config import settings


class EmailService(ABC):
    @abstractmethod
    async def send_otp_email(self, to_email: EmailStr, otp: str) -> bool:
        pass

    @abstractmethod
    async def send_email_bulk(self, to_emails: list[EmailStr]):
        pass


class SendGridEmailService(EmailService):
    def __init__(self) -> None:
        self.sendgrid = SendGridAPIClient(settings.sendgrid_api_key)

    async def send_otp_email(self, to_email: EmailStr, otp: str):
        print(settings)
        message: Mail = Mail(
            from_email=str(settings.sendgrid_from_email),
            to_emails=[str(to_email)],
            subject="Gigger Email Verification.",
            html_content="<strong>and easy to do anywhere, even with Python</strong>",
        )

        message.template_id = "d-e94dcde1e17c46adaf2c08bb0c36e3d8"
        message.dynamic_template_data = {
            "company_name": "Gigger",
            "otp": otp,
            "valid_time": "30",
            "recipient_email": str(to_email),
        }
        try:
            await get_running_loop().run_in_executor(None, self.sendgrid.send, message)
            return True
        except Exception as e:
            logging.error(e)
            raise e

    async def send_email_bulk(self, to_emails: list[EmailStr]):
        pass
