from uuid import UUID

from pydantic import BaseModel, ConfigDict


class HashTag(BaseModel):
    name: str
    uuid: UUID | None = None

    model_config = ConfigDict(
        from_attributes=True,
    )
