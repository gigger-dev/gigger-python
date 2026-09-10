from uuid import UUID

from core.jwt_authenticator import TokenOut
from features.accounts import schemas
from features.accounts.repo import AccountRepo


async def register_usecase(account_repo: AccountRepo, body: schemas.SignUp):
    return await account_repo.register(body=body)


async def sign_in_usecase(
    account_repo: AccountRepo, body: schemas.SignIn
) -> schemas.SignInSuccess:
    return await account_repo.sign_in(body=body)


async def verify_otp_usecase(
    account_repo: AccountRepo, body: schemas.VerifyOTP
) -> TokenOut:
    return await account_repo.verify_otp(body=body)


async def me_usecase(account_repo: AccountRepo, user_uuid: UUID) -> schemas.AccountOut:
    return await account_repo.me(user_uuid=user_uuid)


async def reset_password_request_usecase(
    account_repo: AccountRepo, email: str
) -> schemas.ResetRequestSuccess:
    return await account_repo.reset_password_request(email=email)


async def reset_password_usecase(
    account_repo: AccountRepo, body: schemas.ResetPassword, user_uuid: UUID
) -> TokenOut:
    return await account_repo.reset_password(body=body, user_uuid=user_uuid)


async def refresh_tokens_usecase(
    account_repo: AccountRepo, refresh_token: str
) -> TokenOut:
    return await account_repo.refresh_tokens(refresh_token=refresh_token)


async def forgot_password_request_usecase(
    account_repo: AccountRepo, email: str
) -> schemas.ResetRequestSuccess:
    return await account_repo.forgot_password_request(email=email)


async def forgot_password_usecase(
    account_repo: AccountRepo, body: schemas.ForgotPassword, user_uuid: UUID
) -> TokenOut:
    return await account_repo.forgot_password(body=body, user_uuid=user_uuid)
