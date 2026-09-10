from datetime import UTC, date, datetime
from uuid import UUID

import sqlalchemy as sa
from core.db_model_utils import Base, DateMixin, IDMixin, ModelManager, UUIDMixin
from core.global_import import AsyncSession
from core.password_manager import PasswordHasher
from features.profile.models import Profile
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import schemas


class BlockedToken(Base, IDMixin, UUIDMixin, ModelManager):
    __tablename__ = "gigger_blocked_refresh_tokens"

    refresh_token: Mapped[str] = mapped_column(unique=True)
    expired_at: Mapped[datetime]  # need to clean up after expired.

    @property
    def expired(self) -> bool:
        return datetime.now(UTC) > self.expired_at


class Account(Base, DateMixin, IDMixin, UUIDMixin, ModelManager):
    __tablename__ = "gigger_accounts"

    username: Mapped[str] = mapped_column(
        sa.String(32), unique=True
    )  # do we need more than 32 ?
    email: Mapped[str] = mapped_column(unique=True)
    is_developer: Mapped[bool] = mapped_column(default=False)
    hashed_password: Mapped[str]
    is_banned: Mapped[bool] = mapped_column(default=False)
    is_active: Mapped[bool] = mapped_column(default=True)
    date_of_birth: Mapped[date]
    email_verified: Mapped[bool] = mapped_column(default=False)
    profile: Mapped["Profile"] = relationship(
        "Profile",
        back_populates="account",
        lazy="selectin",
        single_parent=True,
        uselist=False,
    )

    def __repr__(self):
        return f"<Account {self.email}>."

    def to_pydantic(self) -> schemas.AccountOut:
        return schemas.AccountOut.model_validate(self, from_attributes=True)

    def to_pydantic_fewer_details(self) -> schemas.AccountFewerDetailsOut:
        return schemas.AccountFewerDetailsOut(
            username=self.username,
            uuid=self.uuid,
        )

    @classmethod
    async def register(
        cls,
        db_session: AsyncSession,
        body: schemas.SignUp,
    ):
        hashed_password = PasswordHasher().get_password_hash(body.password)
        instance = cls(
            username=body.username,
            email=body.email,
            hashed_password=hashed_password,
            date_of_birth=body.date_of_birth,
        )
        db_session.add(instance)

        await db_session.flush()
        await db_session.commit()
        await db_session.refresh(instance)

        return instance


class AccountFKMixin:
    account_uuid: Mapped[UUID] = mapped_column(
        sa.ForeignKey("gigger_accounts.uuid", ondelete="CASCADE"),
    )


class EmailVerification(Base, IDMixin, UUIDMixin, ModelManager, AccountFKMixin):
    __tablename__ = "gigger_email_verifications"
    opt: Mapped[str] = mapped_column(
        sa.String(6),
    )
    email: Mapped[str]
    attempt: Mapped[int] = mapped_column(default=0)
    dev_mode: Mapped[bool] = mapped_column(default=False)

    __table_args__ = (
        sa.UniqueConstraint("email", "dev_mode", "opt", name="email_dev_mode"),
    )

    def __repr__(self):
        return f"<EmailVerification {self.email}>."
