import json
import uuid as u
from abc import abstractmethod
from datetime import UTC, datetime
from typing import Any, Self

import sqlalchemy as sa
from fastapi.encoders import jsonable_encoder
from features.gig_list.schemas import GigListMedia
from pydantic import BaseModel
from pydantic.json import pydantic_encoder
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from core.global_import import AsyncSession


class Base(AsyncAttrs, DeclarativeBase):
    """
    Base sql model for creating table model.
    """

    type_annotation_map = {
        dict[str, Any]: sa.JSON,
        dict[int, Any]: sa.JSON,
        dict[int, GigListMedia]: sa.JSON,
        dict[str, str]: sa.JSON,
    }

    @abstractmethod
    def to_pydantic(self) -> BaseModel:
        pass

    @classmethod
    @abstractmethod
    def from_pydantic(cls, pydantic_model: BaseModel) -> "Base":
        pass


def now():
    return datetime.now(UTC)


class DateMixin:
    """
    datetime extension for sqlalchemy model.
    """

    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), default=now, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        default=now,
        onupdate=now,
    )


class UUIDMixin:
    """
    uuid extension for sqlalchemy model.
    """

    uuid: Mapped[u.UUID] = mapped_column(
        unique=True,
        index=True,
        default=lambda: u.uuid4(),
    )


class IDMixin:
    """
    id extension for sqlalchemy model.
    """

    id: Mapped[int] = mapped_column(
        sa.Integer,
        primary_key=True,
    )


class PydanticType(sa.types.TypeDecorator):
    """Pydantic type.
    SAVING:
    - Uses SQLAlchemy JSON type under the hood.
    - Acceps the pydantic model and converts it to a dict on save.
    - SQLAlchemy engine JSON-encodes the dict to a string.
    RETRIEVING:
    - Pulls the string from the database.
    - SQLAlchemy engine JSON-decodes the string to a dict.
    - Uses the dict to create a pydantic model.
    """

    # If you work with PostgreSQL, you can consider using
    # sqlalchemy.dialects.postgresql.JSONB instead of a
    # generic sa.types.JSON
    #
    # Ref: https://www.postgresql.org/docs/13/datatype-json.html
    impl = sa.types.JSON

    def __init__(self, pydantic_type):
        super().__init__()
        self.pydantic_type = pydantic_type

    def load_dialect_impl(self, dialect):
        # Use JSONB for PostgreSQL and JSON for other databases.
        if dialect.name == "postgresql":
            return dialect.type_descriptor(JSONB())
        else:
            return dialect.type_descriptor(sa.JSON())

    def process_bind_param(self, value, dialect):
        return jsonable_encoder(value) if value else None

    def process_result_value(self, value, dialect):
        return self.pydantic_type(**value) if value else None


def json_serializer(*args, **kwargs) -> str:
    return json.dumps(*args, default=pydantic_encoder, **kwargs)


class ModelManager:
    @staticmethod
    def set_attr_from_body(instance, **kwargs):
        for field, value in kwargs.items():
            if hasattr(instance, field):
                setattr(instance, field, value)
        return instance

    def set_attr_self(self, **kwargs):
        for field, value in kwargs.items():
            if hasattr(self, field):
                setattr(self, field, value)
        return self

    @classmethod
    async def get(cls, db_session: AsyncSession, **kwargs):
        """
        Get one record from the database by given conditions.

        Args:
        - db_session (AsyncSession): The db session to use.
        - **kwargs: The condition to filter. You can pass the field name and value you want to query.
            For example, to query a record by username, you can pass `username="test"`.
        - selectinload (str): The field name to use selectinload.
        Returns:
        - The queried record if found, otherwise None.

        Raises:
        - AssertionError: If `kwargs` is None.
        """
        assert kwargs is not None, "kwargs cannot be None."
        conditions = []
        for filed, value in kwargs.items():
            if hasattr(cls, filed):
                condition = getattr(cls, filed) == value
                conditions.append(condition)
        if conditions:
            stmt = sa.select(cls).where(sa.and_(*conditions)).limit(1)
            if kwargs.get("selectinload"):
                stmt = stmt.options(sa.orm.selectinload(kwargs["selectinload"]))
            return await db_session.scalar(stmt)

    @classmethod
    async def list(cls, db_session: AsyncSession, **kwargs):
        """
        List records from the database by given conditions by using `and` operator.

        Args:
            db_session (AsyncSession): _description_

        Returns:
            _type_: _description_
        """
        assert kwargs is not None, "kwargs cannot be None."
        conditions = []
        for filed, value in kwargs.items():
            if hasattr(cls, filed):
                condition = getattr(cls, filed) == value
                conditions.append(condition)
        assert conditions, "conditions cannot be empty."
        stmt = sa.select(cls).where(sa.and_(*conditions))
        # Handle order_by safely
        if "order_by" in kwargs and kwargs["order_by"] is not None:
            order_by_clause = kwargs["order_by"]
            stmt = stmt.order_by(
                order_by_clause
            )  # Directly apply the SQLAlchemy order_by object

        if kwargs.get("limit"):
            stmt = stmt.limit(kwargs["limit"])
        if kwargs.get("offset"):
            stmt = stmt.offset(kwargs["offset"])

        result = await db_session.scalars(stmt)
        return result.all()

    @classmethod
    async def delete(cls, db_session: AsyncSession, **kwargs):
        """
        Delete one record from the database by given conditions.

        Args:
        - db_session (AsyncSession): The db session to use.
        - **kwargs: The condition to filter. You can pass the field name and value you want to query.
            For example, to query a record by username, you can pass `username="test"`.
        """
        assert kwargs is not None, "kwargs cannot be None."
        conditions = []
        for filed, value in kwargs.items():
            if hasattr(cls, filed):
                condition = getattr(cls, filed) == value
                conditions.append(condition)
        if conditions:
            stmt = sa.delete(cls).where(sa.and_(*conditions))
            result = await db_session.execute(stmt)
            await db_session.commit()
            return result.rowcount

    async def update(self, db_session: AsyncSession, **kwargs):
        self.set_attr_self(**kwargs)
        await db_session.flush()
        await db_session.commit()
        await db_session.refresh(self)

    @classmethod
    async def create(
        cls,
        db_session: AsyncSession,
        **kwargs,
    ) -> Self | None:
        """_summary_

        Args:
            db_session (AsyncSession): _description_

        Returns:
            _type_: _description_
        Example:
            ```python
            await models.Interest.create(db_session=session, **body.model_dump())
            ```
        """

        # Then option uuid field from pydantic cause error.
        kwargs.pop("uuid", None)

        instance = cls.set_attr_from_body(cls(), **kwargs)

        db_session.add(instance)
        await db_session.flush()
        await db_session.commit()
        await db_session.refresh(instance)
        return instance

    @classmethod
    async def create_if_not_exist(
        cls,
        db_session: AsyncSession,
        **kwargs,
    ) -> Self | None:
        kwargs.pop("uuid", None)
        # instance = await cls.get(db_session=db_session, **kwargs)
        # if instance:
        #     return instance
        # else:
        #     return await cls.create(
        #         db_session=db_session,
        #         **kwargs,
        #     )
        try:
            return await cls.create(
                db_session=db_session,
                **kwargs,
            )
        except IntegrityError:
            await db_session.rollback()
        except Exception as e:
            await db_session.rollback()
            raise e
