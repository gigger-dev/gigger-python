from functools import lru_cache

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing_extensions import Annotated

from core import jwt_authenticator
from core.config import settings
from core.database import DatabaseSessionManager

db_session_manager = DatabaseSessionManager(
    settings.db_url or settings.db_testing_url,
)


async def get_db_session():
    """
    Dependency to get a database session.

    Yields a database session object as a dependency to be used in a FastAPI endpoint.
    """
    async with db_session_manager.session() as session:
        yield session


DbSessionDep = Annotated[AsyncSession, Depends(get_db_session)]


@lru_cache
def get_jwt_authenticator() -> jwt_authenticator.JWTAuthenticator:
    return jwt_authenticator.JWTAuthenticator(
        secret_key=settings.jwt_secret_key or "test_secret_key",
        access_token_expire_minutes=30,
        REFRESH_TOKEN_EXPIRE_DAYS=365,
    )


@lru_cache
def get_stream_chat():
    try:
        import stream_chat

        return stream_chat.StreamChatAsync(
            api_key=settings.get_stream_api_key,
            api_secret=settings.get_stream_api_secret,
        )
    except Exception:
        pass


stream_chat_server_client = get_stream_chat()

jwt_authenticator_dep = get_jwt_authenticator()


__all__ = [
    "DbSessionDep",
    "jwt_authenticator_dep",
    "stream_chat_server_client",
]
