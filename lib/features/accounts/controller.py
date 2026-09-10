from uuid import UUID

from core.global_import import AsyncSession
from core.jwt_authenticator import TokenOut
from features.accounts import schemas, usecases
from features.accounts.repo import AccountRepoImpl


class AccountController:
    def __init__(self, db_session: AsyncSession):
        self._db_session = db_session
        self.repo = AccountRepoImpl(db_session=db_session)

    async def register(self, body: schemas.SignUp) -> schemas.RegisterSuccess:
        return await usecases.register_usecase(account_repo=self.repo, body=body)

    async def sign_in(self, body: schemas.SignIn) -> schemas.SignInSuccess:
        return await usecases.sign_in_usecase(account_repo=self.repo, body=body)

    async def verify_otp(self, body: schemas.VerifyOTP) -> TokenOut:
        return await usecases.verify_otp_usecase(account_repo=self.repo, body=body)

    async def me(self, user_uuid: UUID) -> schemas.AccountOut:
        return await usecases.me_usecase(account_repo=self.repo, user_uuid=user_uuid)

    async def reset_password_request(self, email: str) -> schemas.ResetRequestSuccess:
        return await usecases.reset_password_request_usecase(
            account_repo=self.repo, email=email
        )

    async def reset_password(
        self, body: schemas.ResetPassword, user_uuid: UUID
    ) -> TokenOut:
        return await usecases.reset_password_usecase(
            account_repo=self.repo, body=body, user_uuid=user_uuid
        )

    async def refresh_tokens(self, refresh_token: str) -> TokenOut:
        return await usecases.refresh_tokens_usecase(
            account_repo=self.repo, refresh_token=refresh_token
        )

    async def forgot_password_request(self, email: str) -> schemas.ResetRequestSuccess:
        return await usecases.forgot_password_request_usecase(
            account_repo=self.repo, email=email
        )

    async def forgot_password(
        self, body: schemas.ForgotPassword, user_uuid: UUID
    ) -> TokenOut:
        return await usecases.forgot_password_usecase(
            account_repo=self.repo, body=body, user_uuid=user_uuid
        )
