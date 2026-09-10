import contextlib
import logging
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

# from sqlalchemy import inspect as sqlalchemy_inspect


class DatabaseSessionManager:
    def __init__(self, host: str, engine_kwargs=None):
        if engine_kwargs is None:
            engine_kwargs = {}
        self._engine = (
            create_async_engine(
                host,
                max_overflow=0,
                pool_size=20,
                **engine_kwargs,
            )
            if "postgres" in host
            else create_async_engine(host, **engine_kwargs)
        )
        self._session_maker = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
        self._logger = logging.getLogger(__name__)
        self._logger.setLevel(logging.INFO)

    @property
    def get_engine(self):
        return self._engine

    @property
    def get_session_maker(self):
        return self._session_maker

    async def close(self):
        if self._engine is None:
            raise Exception("DatabaseSessionManager is not initialized.")
        await self._engine.dispose()
        self._engine = None
        self._session_maker = None

    @contextlib.asynccontextmanager
    async def connect(self) -> AsyncIterator[AsyncConnection]:
        if self._engine is None:
            raise Exception("DatabaseSessionManager is not initialized.")
        async with self._engine.begin() as connection:
            try:
                yield connection
            except Exception:
                await connection.rollback()
                raise
            finally:
                await connection.close()

    @contextlib.asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        logging.info("session init.")
        if self._session_maker is None:
            raise Exception("DatabaseSessionManager is not initialized.")
        session = self._session_maker()
        # inspector = sqlalchemy_inspect(session.get_bind())
        # table_names = inspector.get_table_names()
        # self._logger.info("Tables in the database:")
        # for table_name in table_names:
        #     self._logger.info(table_name)
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    async def create_all_base(self, base):
        """For testing usage."""
        if self._engine is None:
            raise Exception("DatabaseSessionManager is not initialized.")
        async with self._engine.begin() as connection:
            await connection.run_sync(base.metadata.drop_all)
            await connection.run_sync(base.metadata.create_all)
