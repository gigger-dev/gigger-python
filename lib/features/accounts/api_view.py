from core.cvb import cbv
from core.dependencies import get_db_session
from core.jwt_authenticator import TokenOut
from core.permissions import get_current_user, is_pre_auth, is_verified_user
from fastapi import APIRouter, Depends
from features.accounts import models, schemas
from features.accounts.controller import AccountController
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

account_router = APIRouter(prefix="/api/v1/accounts", tags=["Accounts"])


@cbv(account_router)
class AccountAPIView:
    def __init__(
        self,
        db_session: AsyncSession = Depends(get_db_session),
    ) -> None:
        self.db_session = db_session
        self.controller = AccountController(db_session=db_session)

    @account_router.post("/register", response_model=schemas.RegisterSuccess)
    async def register(self, body: schemas.SignUp) -> schemas.RegisterSuccess:
        return await self.controller.register(body=body)

    @account_router.post("/sign-in", response_model=schemas.SignInSuccess)
    async def sign_in(self, body: schemas.SignIn) -> schemas.SignInSuccess:
        return await self.controller.sign_in(body=body)

    @account_router.post(
        "/reset-password-request", response_model=schemas.ResetRequestSuccess
    )
    async def reset_password_request(self, email: EmailStr):
        return await self.controller.reset_password_request(email=email)

    # TODO: Add extra auth check
    @account_router.post(
        "/verify-otp",
        response_model=TokenOut,
    )
    async def verify_otp(
        self, body: schemas.VerifyOTP, pre_auth=Depends(is_pre_auth)
    ) -> TokenOut:
        return await self.controller.verify_otp(body=body)

    @account_router.get("/me", response_model=schemas.AccountOut)
    async def me(
        self,
        auth: models.Account = Depends(get_current_user),
    ) -> schemas.AccountOut:
        return auth.to_pydantic()

    @account_router.post("/dev/delete_account")
    async def delete_account(self, email: EmailStr):
        # dev_list = [
        #     "thitlwincoder@gmail.com",
        #     "b14cknc0d3@gmail.com",
        #     "darkdader@gmail.com",
        #     "alessio.davi@gmail.com",
        #     "hlatz523@gmail.com",
        # ]
        # if email not in dev_list:
        #     raise HTTPException(
        #         status_code=status.HTTP_401_UNAUTHORIZED,
        #     )
        return await models.Account.delete(db_session=self.db_session, email=email)

    @account_router.post("/reset-password")
    async def reset_password(
        self,
        body: schemas.ResetPassword,
        account: models.Account = Depends(is_verified_user),
    ) -> TokenOut:
        return await self.controller.reset_password(body=body, user_uuid=account.uuid)

    @account_router.post("/refresh-tokens")
    async def refresh_tokens(self, refresh_token: str) -> TokenOut:
        return await self.controller.refresh_tokens(refresh_token=refresh_token)

    # @account_router.post("/resend-otp")
    # async def resend_otp(self, email: EmailStr):
    #     return await self.controller.resend_otp(email=email)
    @account_router.post(
        "/forgot-password-request", response_model=schemas.ResetRequestSuccess
    )
    async def forgot_password_request(self, email: EmailStr):
        return await self.controller.forgot_password_request(email=email)

    @account_router.post("/forgot-password")
    async def forgot_password(
        self,
        body: schemas.ForgotPassword,
        account: models.Account = Depends(is_verified_user),
    ) -> TokenOut:
        return await self.controller.forgot_password(body=body, user_uuid=account.uuid)
