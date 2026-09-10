from abc import ABC, abstractmethod
from uuid import UUID

from core.config import settings
from core.dependencies import jwt_authenticator_dep
from core.email_service import SendGridEmailService
from core.global_import import AsyncSession
from core.jwt_authenticator import JWTUserInfo, TokenOut
from core.password_manager import PasswordHasher
from core.utils import generate_otp_code, is_dev_mode
from fastapi import HTTPException, status
from features.accounts import models, schemas
from pydantic import EmailStr
from sqlalchemy.exc import IntegrityError


class AccountRepo(ABC):
    @abstractmethod
    async def register(self, body: schemas.SignUp) -> schemas.RegisterSuccess:
        pass

    @abstractmethod
    async def sign_in(self, body: schemas.SignIn) -> schemas.SignInSuccess:
        pass

    @abstractmethod
    async def verify_otp(self, body: schemas.VerifyOTP) -> TokenOut:
        pass

    @abstractmethod
    async def resend_otp(self, email: EmailStr) -> TokenOut:
        pass

    @abstractmethod
    async def reset_password(
        self, body: schemas.ResetPassword, user_uuid: UUID
    ) -> TokenOut:
        pass

    @abstractmethod
    async def reset_password_request(
        self, email: EmailStr
    ) -> schemas.ResetRequestSuccess:
        pass

    @abstractmethod
    async def forgot_password(
        self, body: schemas.ForgotPassword, user_uuid: UUID
    ) -> TokenOut:
        pass

    @abstractmethod
    async def forgot_password_request(
        self, email: EmailStr
    ) -> schemas.ResetRequestSuccess:
        pass

    @abstractmethod
    async def refresh_tokens(self, refresh_token: str) -> TokenOut:
        pass

    @abstractmethod
    async def me(
        self, user_uuid: UUID, email: EmailStr | None = None
    ) -> schemas.AccountOut:
        pass


class AccountRepoImpl(AccountRepo):
    def __init__(self, db_session: AsyncSession) -> None:
        self.db_session = db_session

    async def register(self, body: schemas.SignUp) -> schemas.RegisterSuccess:
        try:
            # steps1 register
            result = await models.Account.register(
                db_session=self.db_session,
                body=body,
            )
            if result:
                # step.2 generate session token
                session_token = (
                    jwt_authenticator_dep.create_access_token_only_with_email(
                        email=result.email
                    )
                )
                # step.2 save verification and otp
                otp_code = generate_otp_code(result.email)

                verification = await models.EmailVerification.create(
                    db_session=self.db_session,
                    **schemas.EmailVerificationIn(
                        email=result.email,
                        opt=otp_code,
                        account_uuid=result.uuid,
                    ).model_dump(),
                    dev_mode=is_dev_mode(result.email),
                )
                assert verification
                # step.3 send email.
                if not settings.debug and not verification.dev_mode:
                    mail_service = SendGridEmailService()
                    await mail_service.send_otp_email(
                        to_email=result.email, otp=otp_code
                    )

                # TODO: send email
                return schemas.RegisterSuccess(
                    email=result.email, session_token=session_token
                )

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="username or email already exists.",
            )
        except IntegrityError as e:
            await self.db_session.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"username or email already exists. {e}",
            )

        except Exception as e:
            await self.db_session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Something went wrong. {e}",
            )

    async def sign_in(self, body: schemas.SignIn) -> schemas.SignInSuccess:
        # 1 check user using email
        has_user = await models.Account.get(
            db_session=self.db_session, email=body.email
        )

        if not has_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid email or password.",
            )

        if not has_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is not active.",
            )

        if has_user.is_banned:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is banned.",
            )

        if not has_user.email_verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Email is not verified.",
            )

        # 2 check password
        if not PasswordHasher().verify_password(
            body.password, has_user.hashed_password
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid email or password.",
            )

        # 3 generate session token
        access_token = jwt_authenticator_dep.create_access_token_only_with_email(
            email=has_user.email
        )
        # check dev mode verification.
        check_verification = await models.EmailVerification.get(
            db_session=self.db_session, email=has_user.email
        )

        if check_verification and check_verification.dev_mode:
            return schemas.SignInSuccess(
                email=has_user.email, session_token=access_token
            )
        # 4 create verification
        # delete old verification
        if check_verification:
            await models.EmailVerification.delete(
                db_session=self.db_session, uuid=check_verification.uuid
            )

        otp_code = generate_otp_code(body.email)

        # create new verification
        await models.EmailVerification.create(
            db_session=self.db_session,
            **schemas.EmailVerificationIn(
                email=has_user.email,
                opt=otp_code,
                account_uuid=has_user.uuid,
            ).model_dump(),
            dev_mode=is_dev_mode(has_user.email),
        )
        # 5 send email
        if not settings.debug:
            mail_service = SendGridEmailService()
            await mail_service.send_otp_email(to_email=has_user.email, otp=otp_code)
        # 7 return session token
        if not has_user.email_verified:
            return schemas.SignInSuccess(
                email=has_user.email, session_token=access_token
            )

        return schemas.SignInSuccess(email=has_user.email, session_token=access_token)

    async def verify_otp(self, body: schemas.VerifyOTP) -> TokenOut:
        verification = await models.EmailVerification.get(
            db_session=self.db_session, email=body.email
        )
        if not verification:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid OTP or request.",
            )

        if verification.attempt >= 5:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Too many OTP attempts.",
            )

        if verification.opt != body.otp:
            # if has email verification but wrong otp increase the count.
            if verification:
                await verification.update(
                    db_session=self.db_session, attempt=verification.attempt + 1
                )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid OTP or request.",
            )

        # Delete the verification record after successful verification.
        # But in dev mode, don't delete the record.
        if not verification.dev_mode:
            await models.EmailVerification.delete(
                db_session=self.db_session, uuid=verification.uuid
            )
        # check email verification status on account
        account = await models.Account.get(
            db_session=self.db_session, uuid=verification.account_uuid
        )
        if not account:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid OTP or request.",
            )
        if not account.email_verified:
            await account.update(db_session=self.db_session, email_verified=True)

        return jwt_authenticator_dep.create_tokens(
            user_info=JWTUserInfo(
                uuid=str(verification.uuid),
                email=verification.email,
                sub=verification.email,
            )
        )

    async def resend_otp(self, email: EmailStr) -> TokenOut:
        raise NotImplementedError

    async def refresh_tokens(self, refresh_token: EmailStr) -> TokenOut:
        # 1. check whether the refresh token is valid. or blocked.
        blocked = await models.BlockedToken.get(
            db_session=self.db_session, refresh_token=refresh_token
        )
        if blocked:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Refresh token is blocked.",
            )

        # 2. decode the refresh token
        # 3. check if it is about to expire
        return jwt_authenticator_dep.refresh_tokens(refresh_token=refresh_token)

    async def me(
        self, user_uuid: UUID, email: EmailStr | None = None
    ) -> schemas.AccountOut:
        if email:
            result = await models.Account.get(
                db_session=self.db_session, email=str(email)
            )
        else:
            result = await models.Account.get(
                db_session=self.db_session, uuid=user_uuid
            )
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Account not found."
            )
        return result.to_pydantic()

    async def reset_password(
        self, body: schemas.ResetPassword, user_uuid: UUID
    ) -> TokenOut:
        # TODO: block old refresh token
        # 1 check pass
        account = await models.Account.get(db_session=self.db_session, uuid=user_uuid)
        if not account:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account not found.",
            )
        if not PasswordHasher().verify_password(
            body.old_password, account.hashed_password
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid password.",
            )

        # 2 create new password
        new_hashed_password = PasswordHasher().get_password_hash(body.password)

        # 3 update password
        await account.update(
            db_session=self.db_session,
            hashed_password=new_hashed_password,
        )

        # 4 return token
        return jwt_authenticator_dep.create_tokens(
            user_info=JWTUserInfo(
                uuid=str(account.uuid),
                email=account.email,
                sub=account.email,
            )
        )

    async def reset_password_request(
        self, email: EmailStr
    ) -> schemas.ResetRequestSuccess:
        has_user = await models.Account.get(
            db_session=self.db_session, email=str(email)
        )
        if not has_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid email.",
            )
        otp_code = generate_otp_code(str(email))
        access_token = jwt_authenticator_dep.create_access_token_only_with_email(
            email=has_user.email
        )
        check_verification = await models.EmailVerification.get(
            db_session=self.db_session, email=has_user.email
        )
        if check_verification and check_verification.dev_mode:
            return schemas.ResetRequestSuccess(
                email=has_user.email,
                session_token=access_token,
            )
        if check_verification:
            await models.EmailVerification.delete(
                db_session=self.db_session, uuid=check_verification.uuid
            )
        await models.EmailVerification.create(
            db_session=self.db_session,
            **schemas.EmailVerificationIn(
                email=has_user.email,
                opt=otp_code,
                account_uuid=has_user.uuid,
            ).model_dump(),
            dev_mode=is_dev_mode(has_user.email),
        )
        if not settings.debug:
            mail_service = SendGridEmailService()
            await mail_service.send_otp_email(to_email=has_user.email, otp=otp_code)
        return schemas.ResetRequestSuccess(
            email=has_user.email,
            session_token=access_token,
        )

    async def forgot_password_request(
        self, email: EmailStr
    ) -> schemas.ResetRequestSuccess:
        has_user = await models.Account.get(
            db_session=self.db_session, email=str(email)
        )
        if not has_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid email.",
            )
        otp_code = generate_otp_code(str(email))
        access_token = jwt_authenticator_dep.create_access_token_only_with_email(
            email=has_user.email
        )
        check_verification = await models.EmailVerification.get(
            db_session=self.db_session, email=has_user.email
        )
        if check_verification and check_verification.dev_mode:
            return schemas.ResetRequestSuccess(
                email=has_user.email,
                session_token=access_token,
            )
        if check_verification:
            await models.EmailVerification.delete(
                db_session=self.db_session, uuid=check_verification.uuid
            )
        await models.EmailVerification.create(
            db_session=self.db_session,
            **schemas.EmailVerificationIn(
                email=has_user.email,
                opt=otp_code,
                account_uuid=has_user.uuid,
            ).model_dump(),
            dev_mode=is_dev_mode(has_user.email),
        )
        if not settings.debug:
            mail_service = SendGridEmailService()
            await mail_service.send_otp_email(to_email=has_user.email, otp=otp_code)
        return schemas.ResetRequestSuccess(
            email=has_user.email,
            session_token=access_token,
        )

    async def forgot_password(
        self, body: schemas.ForgotPassword, user_uuid: UUID
    ) -> TokenOut:
        account = await models.Account.get(db_session=self.db_session, uuid=user_uuid)
        if not account:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account not found.",
            )

        # 1 create new password
        new_hashed_password = PasswordHasher().get_password_hash(body.password)

        # 2 update password
        await account.update(
            db_session=self.db_session,
            hashed_password=new_hashed_password,
        )

        # 4 return token
        return jwt_authenticator_dep.create_tokens(
            user_info=JWTUserInfo(
                uuid=str(account.uuid),
                email=account.email,
                sub=account.email,
            )
        )
