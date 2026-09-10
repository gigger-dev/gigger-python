from uuid import UUID

from core.global_import import AsyncSession
from core.response import SimpleResponse
from features.sup import schemas
from features.sup.repo import SupRepoImpl
from features.sup.usecases import (
    create_sup_usecase,
    delete_sup_usecase,
    get_sup_by_uuid_usecase,
    get_sup_metadata_usecase,
    like_unlike_sup_usecase,
    list_profile_having_sup_usecase,
    list_sup_usecase,
    share_sup_usecase,
    view_sup_usecase,
)


class SupController:
    def __init__(self, db_session: AsyncSession):
        self.repo = SupRepoImpl(db_session=db_session)

    async def create_sup(self, body: schemas.SupCreate):
        return await create_sup_usecase(repo=self.repo, body=body)

    async def list_sup(
        self, profile_uuid: UUID, created_from: schemas.SupCreatedFromEnum
    ):
        return await list_sup_usecase(
            repo=self.repo, profile_uuid=profile_uuid, created_from=created_from
        )

    async def list_profile_having_sup(
        self,
        profile_uuid: UUID,
        limit: int,
        offset: int,
        created_from: schemas.SupCreatedFromEnum,
    ):
        return await list_profile_having_sup_usecase(
            repo=self.repo,
            profile_uuid=profile_uuid,
            limit=limit,
            offset=offset,
            created_from=created_from,
        )

    async def delete_sup(self, sup_uuid: UUID, profile_uuid: UUID) -> SimpleResponse:
        return await delete_sup_usecase(
            repo=self.repo, sup_uuid=sup_uuid, profile_uuid=profile_uuid
        )

    async def like_unlike_sup(
        self,
        logged_in_profile_uuid: UUID,
        liker_uuid: UUID,
        sup_uuid: UUID,
    ):
        return await like_unlike_sup_usecase(
            repo=self.repo,
            logged_in_profile_uuid=logged_in_profile_uuid,
            liker_uuid=liker_uuid,
            sup_uuid=sup_uuid,
        )

    async def get_sup_metadata(
        self,
        sup_uuid: UUID,
        logged_in_profile_uuid: UUID,
        viewer_uuid: UUID,
    ):
        return await get_sup_metadata_usecase(
            repo=self.repo,
            sup_uuid=sup_uuid,
            logged_in_profile_uuid=logged_in_profile_uuid,
            viewer_uuid=viewer_uuid,
        )

    async def share_sup(
        self,
        logged_in_profile_uuid: UUID,
        sharer_uuid: UUID,
        sup_uuid: UUID,
    ):
        return await share_sup_usecase(
            repo=self.repo,
            logged_in_profile_uuid=logged_in_profile_uuid,
            sharer_uuid=sharer_uuid,
            sup_uuid=sup_uuid,
        )

    async def get_sup_by_uuid(self, sup_uuid: UUID):
        return await get_sup_by_uuid_usecase(repo=self.repo, sup_uuid=sup_uuid)

    async def view_sup(
        self,
        logged_in_profile_uuid: UUID,
        viewer_uuid: UUID,
        sup_uuid: UUID,
    ):
        return await view_sup_usecase(
            repo=self.repo,
            logged_in_profile_uuid=logged_in_profile_uuid,
            viewer_uuid=viewer_uuid,
            sup_uuid=sup_uuid,
        )
