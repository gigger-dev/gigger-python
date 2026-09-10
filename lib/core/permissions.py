from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from features.accounts import models
from jose import JWTError

from core.dependencies import get_db_session, jwt_authenticator_dep
from core.global_import import AsyncSession
from core.jwt_authenticator import JWTUserInfo

auth_scheme = HTTPBearer()
credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)
account_banned_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Your account is banned.",
    headers={"WWW-Authenticate": "Bearer"},
)


def is_pre_auth(
    auth_header: HTTPAuthorizationCredentials = Depends(auth_scheme),
) -> str:
    credentials = auth_header.credentials
    try:
        payload = jwt_authenticator_dep.verify_access_token_only_with_email(
            token=credentials
        )

        if not payload:
            raise credentials_exception
        result = payload.get("sub")

        if not result:
            raise credentials_exception
        return result
    except JWTError:
        raise credentials_exception


async def get_current_user(
    auth_header: HTTPAuthorizationCredentials = Depends(auth_scheme),
    db_session: AsyncSession = Depends(get_db_session),
):
    credentials = auth_header.credentials

    try:
        payload = jwt_authenticator_dep.verify_access_token(token=credentials)

        if not payload or not isinstance(payload, JWTUserInfo):
            raise credentials_exception
        result = payload.email
        account = await models.Account.get(db_session, email=result)

        if not account:
            raise credentials_exception
        if account.is_banned:
            raise account_banned_exception
        return account

    except JWTError:
        raise credentials_exception


async def is_verified_user(account: models.Account = Depends(get_current_user)):
    if not account.email_verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email is not verified.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return account


# TODO : check pro user permissions
