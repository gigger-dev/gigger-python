import re
from datetime import date
from uuid import UUID

from pydantic import BaseModel, EmailStr, ValidationInfo, field_validator


class EmailVerificationIn(BaseModel):
    opt: str
    email: EmailStr
    account_uuid: UUID


class EmailVerificationInDev(EmailVerificationIn):
    opt: str
    email: EmailStr
    account_uuid: UUID
    dev_mode: bool


class SignIn(BaseModel):
    email: EmailStr
    password: str

    @field_validator("password")
    def validate_password(cls, password: str):
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters.")
        if not any(char.isupper() for char in password):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(char.islower() for char in password):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(char.isdigit() for char in password):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r"[!@#$%^&*()_+{}:;<>,.?/~`-]", password):
            raise ValueError("Password must contain at least one special character")

        return password


class SignUp(SignIn):
    username: str
    confirm_password: str
    date_of_birth: date

    @field_validator("confirm_password")
    def match_passwords(cls, confirm_password: str, info: ValidationInfo):
        if "password" in info.data and confirm_password == info.data["password"]:
            return confirm_password
        raise ValueError("Passwords don't match.")

    @field_validator("username")
    def validate_username(cls, username: str):
        if len(username) < 4:
            raise ValueError("Username must be at least 3 characters.")
        # add more validations

        return username


class AccountOut(BaseModel):
    username: str
    email: EmailStr
    is_active: bool
    date_of_birth: date
    email_verified: bool
    uuid: UUID


class AccountFewerDetailsOut(BaseModel):
    username: str
    uuid: UUID


class RegisterSuccess(BaseModel):
    email: EmailStr
    session_token: str


class SignInSuccess(RegisterSuccess):
    pass


class ResetRequestSuccess(RegisterSuccess):
    pass


class VerifyOTP(BaseModel):
    email: EmailStr
    otp: str

    @field_validator("otp")
    def validate_otp(cls, otp: str):
        if len(otp) != 6:
            raise ValueError("OTP must be 6 digits.")
        return otp


class ResetPassword(BaseModel):
    old_password: str
    password: str
    confirm_password: str

    @field_validator("confirm_password")
    def match_passwords(cls, confirm_password: str, info: ValidationInfo):
        if "password" in info.data and confirm_password == info.data["password"]:
            return confirm_password
        raise ValueError("Passwords don't match.")

    @field_validator("password")
    def validate_password(cls, password: str):
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters.")
        if not any(char.isupper() for char in password):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(char.islower() for char in password):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(char.isdigit() for char in password):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r"[!@#$%^&*()_+{}:;<>,.?/~`-]", password):
            raise ValueError("Password must contain at least one special character")

        return password

    @field_validator("old_password")
    def validate_old_password(cls, password: str):
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters.")
        if not any(char.isupper() for char in password):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(char.islower() for char in password):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(char.isdigit() for char in password):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r"[!@#$%^&*()_+{}:;<>,.?/~`-]", password):
            raise ValueError("Password must contain at least one special character")

        return password


class ForgotPassword(BaseModel):
    password: str
    confirm_password: str

    @field_validator("confirm_password")
    def match_passwords(cls, confirm_password: str, info: ValidationInfo):
        if "password" in info.data and confirm_password == info.data["password"]:
            return confirm_password
        raise ValueError("Passwords don't match.")

    @field_validator("password")
    def validate_password(cls, password: str):
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters.")
        if not any(char.isupper() for char in password):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(char.islower() for char in password):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(char.isdigit() for char in password):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r"[!@#$%^&*()_+{}:;<>,.?/~`-]", password):
            raise ValueError("Password must contain at least one special character")

        return password
