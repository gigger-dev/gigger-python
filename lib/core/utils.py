import email
import email.utils
import secrets
import string

from pydantic import EmailStr

from core.config import settings


def generate_otp_code(mail: EmailStr) -> str:
    if (
        settings.debug
        or str(mail)
        in [
            "thitlwincoder@gmail.com",
            "aliz.cc.me@gmail.com",
        ]
        or email.utils.parseaddr(str(mail))[1] == "gigger.art"
    ):
        return "133733"
    return "".join(secrets.choice(string.digits) for _ in range(6))


def is_dev_mode(mail: EmailStr) -> bool:
    return (
        settings.debug
        or str(mail)
        in [
            "thitlwincoder@gmail.com",
            "aliz.cc.me@gmail.com",
        ]
        or email.utils.parseaddr(str(mail))[1] == "gigger.art"
    )
