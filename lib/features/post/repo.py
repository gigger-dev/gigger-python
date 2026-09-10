import logging
from abc import ABC, abstractmethod
from typing import List, Tuple
from uuid import UUID

import sqlalchemy as sa
from core import schemas as core_schemas
from core.config import settings
from core.fileupload import delete_file_from_s3
from core.global_import import AsyncSession
from core.response import PaginatedResponse, SimpleResponse
from fastapi import HTTPException
from features.accounts.models import Account
from features.gig_list.models import GigList
from features.post import models, schemas
from features.profile.models import Profile
from features.settings.models import Notification
from features.settings.schemas import (
    NotificationBodySchema,
    NotificationDataType,
    NotificationIn,
    NotificationType,
)


class PostRepo(ABC):
    @abstractmethod
    async def search_hash_tags(self, query: str) -> list[core_schemas.HashTag]:
        pass

    # @abstractmethod
    # async def create_hash_tags(
    #     self, body: List[schemas.HashTag]
    # ) -> list[schemas.HashTag]:
    #     pass

    @abstractmethod
    async def create_post(self, body: schemas.PostCreate) -> schemas.PostOut:
        pass

    @abstractmethod
    async def delete_post(self, post_uuid: UUID, profile_uuid: UUID) -> SimpleResponse:
        pass

    @abstractmethod
    async def list_posts(
        self,
        profile_uuid: UUID,
    ) -> PaginatedResponse[schemas.PostOut]:
        pass

    @abstractmethod
    async def list_posts_by_profile(self, profile_uuid: UUID) -> List[schemas.PostOut]:
        pass

    @abstractmethod
    async def update_post(self, body: schemas.PostUpdate) -> schemas.PostOut:
        pass

    @abstractmethod
    async def list_posts_for_given_profile(
        self,
        profile_uuid: UUID,
        limit: int,
        offset: int,
    ) -> PaginatedResponse[schemas.PostOut]:
        pass

    @abstractmethod
    async def list_others_posts(
        self, profile_uuid: UUID, viewer_profile_uuid: UUID
    ) -> list[schemas.PostOut]:
        pass

    @abstractmethod
    async def upsert_post_position_metadata(
        self, body: schemas.PostPositionMetadata
    ) -> schemas.PostPositionMetadata:
        pass

    @abstractmethod
    async def get_layout(self, profile_uuid: UUID) -> schemas.PostPositionMetadata:
        pass

    @abstractmethod
    async def view_post(
        self,
        logged_in_profile_uuid: UUID,
        viewer_uuid: UUID,
        post_uuid: UUID,
    ) -> schemas.PostMetadata:
        pass

    @abstractmethod
    async def get_metadata(
        self,
        post_uuid: UUID,
        logged_in_profile_uuid: UUID,
        viewer_uuid: UUID,
    ) -> schemas.PostMetadata:
        pass

    @abstractmethod
    async def get_post_by_uuid(
        self,
        post_uuid: UUID,
    ) -> schemas.PostOut:
        pass

    @abstractmethod
    async def like_unlike_post(
        self,
        post_uuid: UUID,
        logged_in_profile_uuid: UUID,
        liker_uuid: UUID,
    ) -> schemas.PostMetadata:
        pass

    @abstractmethod
    async def search_post(
        self,
        searcher_uuid: UUID,
        title: str,
        keywords: str,
        genre: core_schemas.HashTag | None,
        limit: int,
        offset: int,
    ) -> PaginatedResponse[schemas.PostOut]:
        pass

    @abstractmethod
    async def search_all(
        self, searcher_uuid: UUID, keyword: str
    ) -> schemas.AllSearchResults:
        pass

    @abstractmethod
    async def get_all_self_post(
        self,
        profile_uuid: UUID,
    ) -> list[schemas.PostOut]:
        pass


class PostRepoImpl(PostRepo):
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def _upsert_tagged_profile(
        self,
        tagged_profiles: List[UUID],
        post: models.Post,
        is_update: bool = False,
    ):
        if self.db_session.bind.dialect.name == "postgresql":
            import sqlalchemy.dialects.postgresql as pa

            stmt = (
                pa.insert(models.post_mentions_many_to_many)
                .values(
                    [
                        {"post_uuid": post.uuid, "profile_uuid": p_uid}
                        for p_uid in tagged_profiles
                    ]
                )
                .on_conflict_do_nothing(
                    index_elements=["post_uuid", "profile_uuid"],
                )
            )
        elif self.db_session.bind.dialect.name == "sqlite":
            import sqlalchemy.dialects.sqlite as sa

            stmt = (
                sa.insert(models.post_mentions_many_to_many)
                .values(
                    [
                        {"post_uuid": post.uuid, "profile_uuid": p_uid}
                        for p_uid in tagged_profiles
                    ]
                )
                .on_conflict_do_nothing(
                    index_elements=["post_uuid", "profile_uuid"],
                )
            )
        else:
            raise HTTPException(status_code=500, detail="Unsupported database dialect.")
        await self.db_session.execute(stmt)
        await self.db_session.commit()
        profile = await Profile.get(db_session=self.db_session, uuid=post.profile_uuid)
        if not profile:
            logging.warning(f"No Profile({post.profile_uuid}) ${post.uuid}.")

        else:
            if is_update:
                return
            await Notification.setup_and_send_notifications(
                db_session=self.db_session,
                profile_uuid_to_send_notification=[b for b in tagged_profiles],
                notification_body=NotificationBodySchema(
                    notification_type=NotificationType.NEW_MENTION.value,
                    notification_data_type=NotificationDataType.POST.value,
                    profile_uuid=str(post.profile_uuid),
                    profile_name=profile.account.username,
                    profile_image=profile.avatar_media,
                    uuid=str(post.uuid),
                ),
                notification_data_type=NotificationDataType.POST,
            )

    async def search_hash_tags(self, query: str) -> list[core_schemas.HashTag]:
        result = await self.db_session.scalars(
            sa.select(models.HashTag)
            .where(models.HashTag.name.ilike(f"%{query}%"))
            .order_by(
                models.HashTag.name.ilike(f"{query}%").desc(),
                models.HashTag.name,
            )
            .limit(50)
        )
        return [result.to_pydantic() for result in result.all()]

    async def create_post(self, body: schemas.PostCreate) -> schemas.PostOut:
        # 1. get total post count
        # 2. if post > 9 update oldest post to archive
        # 3. create new post

        result = await models.Post.create_post(db_session=self.db_session, body=body)

        if not result:
            raise HTTPException(status_code=500, detail="Failed to create post!")

        for hash_tag in body.hashtags:
            if not hash_tag.uuid and hash_tag.name not in [
                h.name for h in result.hashtags
            ]:
                hash_tag_created = await models.HashTag.create_if_not_exist(
                    db_session=self.db_session, **hash_tag.model_dump(exclude_none=True)
                )
                if hash_tag_created:
                    result.hashtags.append(hash_tag_created)

                else:
                    hash_tag_search = await models.HashTag.get(
                        db_session=self.db_session, name=hash_tag.name
                    )
                    if hash_tag_search:
                        result.hashtags.append(hash_tag_search)

            else:
                if hash_tag.uuid in [uuids for uuids in result.hashtags]:
                    continue
                get_has_tag = await models.HashTag.get(
                    db_session=self.db_session, uuid=hash_tag.uuid
                )
                if get_has_tag:
                    result.hashtags.append(get_has_tag)
            await self.db_session.flush()
            await self.db_session.commit()
            await self.db_session.refresh(result)
        for profile in body.tagged_profiles:
            await self._upsert_tagged_profile(body.tagged_profiles, post=result)
        await self.db_session.refresh(result)

        return result.to_pydantic()

    async def list_posts(
        self, profile_uuid: UUID
    ) -> PaginatedResponse[schemas.PostOut]:
        """_summary_
        For fab9, self.

        Args:
            profile_uuid (UUID): _description_

        Returns:
            PaginatedResponse[schemas.PostOut]: _description_
        """
        stmt = (
            sa.select(models.Post).where(
                models.Post.profile_uuid == profile_uuid,
                models.Post.is_private.is_(False),
            )
            # .join(
            #     models.HashTag,
            #     models.HashTag.uuid == models.post_hashtags_many_to_many.c.hashtag_uuid,
            # )
            # .options(
            #     joinedload(models.Post.hashtags),
            # )
        )
        result = await self.db_session.execute(stmt)
        items = [result.to_pydantic() for result in result.scalars().unique().all()]
        return PaginatedResponse(
            total=len(items),
            limit=50,
            offset=0,
            items=items,
        )

    async def list_posts_by_profile(self, profile_uuid: UUID) -> list[schemas.PostOut]:
        stmt = (
            sa.select(models.Post)
            .where(
                models.Post.profile_uuid == profile_uuid,
                models.Post.is_private.is_(False),
            )
            .join(
                models.post_hashtags_many_to_many,
                models.Post.uuid == models.post_hashtags_many_to_many.c.post_uuid,
            )
            .join(
                models.HashTag,
                models.HashTag.uuid == models.post_hashtags_many_to_many.c.hashtag_uuid,
            )
        )
        result = await self.db_session.execute(stmt)
        return [result.to_pydantic() for result in result.scalars().unique().all()]

    async def update_post(self, body: schemas.PostUpdate) -> schemas.PostOut:
        post = await models.Post.get(db_session=self.db_session, uuid=body.uuid)
        if not post:
            raise HTTPException(status_code=404, detail="Post not found!")
        post_body = body.model_dump(
            exclude={"uuid", "profile_uuid", "hashtags", "tagged_profiles"},
            exclude_none=True,
        )

        await post.update(
            db_session=self.db_session,
            **post_body,
        )
        # TODO: kz implement remove hashtag see below (body.tagged_profiles).
        if body.hashtags:
            for hash_tag in body.hashtags:
                # check uuid and name,
                if not hash_tag.uuid and hash_tag.name not in [
                    h.name for h in post.hashtags
                ]:
                    hash_tag_created = await models.HashTag.create_if_not_exist(
                        db_session=self.db_session,
                        **hash_tag.model_dump(exclude_none=True),
                    )
                    if hash_tag_created:
                        post.hashtags.append(hash_tag_created)

                    else:
                        hash_tag_search = await models.HashTag.get(
                            db_session=self.db_session, name=hash_tag.name
                        )
                        if hash_tag_search:
                            post.hashtags.append(hash_tag_search)

                else:
                    if hash_tag.uuid in [uuids for uuids in post.hashtags]:
                        continue
                    get_has_tag = await models.HashTag.get(
                        db_session=self.db_session, uuid=hash_tag.uuid
                    )
                    if get_has_tag:
                        post.hashtags.append(get_has_tag)

        if body.tagged_profiles:
            await self._upsert_tagged_profile(
                tagged_profiles=body.tagged_profiles,
                post=post,
                is_update=True,
            )

        await self.db_session.flush()
        await self.db_session.commit()
        await self.db_session.refresh(post)

        return post.to_pydantic()

    async def delete_post(self, post_uuid: UUID, profile_uuid: UUID) -> SimpleResponse:
        post = await models.Post.get(
            db_session=self.db_session,
            uuid=post_uuid,
            profile_uuid=profile_uuid,
        )
        if not post:
            raise HTTPException(status_code=404, detail="Post not found!")
        if not settings.debug:
            try:
                if post.thumbnail_url:
                    await delete_file_from_s3(post.thumbnail_url)
            except Exception as e:
                print(f"Error deleting thumbnail image {post.thumbnail_url}: {e}")
            try:
                if post.video_url:
                    await delete_file_from_s3(post.video_url)
            except Exception as e:
                print(f"Error deleting video file {post.video_url}: {e}")
        await post.delete(db_session=self.db_session, uuid=post_uuid)
        return SimpleResponse(message="Post deleted successfully!", status_code=200)

    async def list_posts_for_given_profile(
        self, profile_uuid: UUID, limit: int = 100, offset: int = 0
    ):
        profile = await Profile.get(db_session=self.db_session, uuid=profile_uuid)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found!")
        user_interest = [interest.name for interest in profile.interests]

        hash_tags_query_expr = sa.func.lower(models.HashTag.name).in_(user_interest)

        total_items = 0
        stmt = (
            sa.select(models.Post)
            .join(
                models.post_hashtags_many_to_many,
                models.Post.uuid == models.post_hashtags_many_to_many.c.post_uuid,
            )
            .join(
                models.HashTag,
                models.HashTag.uuid == models.post_hashtags_many_to_many.c.hashtag_uuid,
            )
            .where(
                models.Post.is_draft.is_(False),
                models.Post.is_membership_only.is_(False),
                models.Post.is_only_for_followers.is_(False),
                models.Post.is_private.is_(False),
                hash_tags_query_expr,
            )
        )
        count_stmt: sa.Select[Tuple[int]] = sa.select(sa.func.count()).select_from(
            stmt.subquery()
        )

        total_items = await self.db_session.scalar(count_stmt)
        if not total_items:
            stmt = (
                sa.select(models.Post)
                .join(
                    models.post_hashtags_many_to_many,
                    models.Post.uuid == models.post_hashtags_many_to_many.c.post_uuid,
                )
                .join(
                    models.HashTag,
                    models.HashTag.uuid
                    == models.post_hashtags_many_to_many.c.hashtag_uuid,
                )
                # .options(
                #     joinedload(models.Post.hashtags),
                # )
                .where(
                    models.Post.is_draft.is_(False),
                    models.Post.is_membership_only.is_(False),
                    models.Post.is_only_for_followers.is_(False),
                    models.Post.is_private.is_(False),
                )
            )

            count_stmt: sa.Select[Tuple[int]] = sa.select(sa.func.count()).select_from(
                stmt.subquery()
            )

            total_items = await self.db_session.scalar(count_stmt)

            item_stmt = stmt.offset(offset).limit(limit).order_by(sa.func.random())

            items = await self.db_session.execute(item_stmt)

            return PaginatedResponse(
                limit=limit,
                offset=offset,
                total=total_items or 0,
                items=[i.to_pydantic() for i in items.scalars().unique().all()],
            )

        item_stmt = stmt.offset(offset).limit(limit).order_by(sa.func.random())

        items = await self.db_session.execute(item_stmt)

        return PaginatedResponse(
            limit=limit,
            offset=offset,
            total=total_items or 0,
            items=[i.to_pydantic() for i in items.scalars().unique().all()],
        )

    async def list_others_posts(
        self, profile_uuid: UUID, viewer_profile_uuid: UUID
    ) -> list[schemas.PostOut]:
        # TODO: check blocked or not
        # TODO: check only follower or not
        select = (
            (
                sa.select(models.Post).where(
                    models.Post.profile_uuid == profile_uuid,
                    models.Post.is_draft.is_(False),
                    models.Post.is_membership_only.is_(False),
                    models.Post.is_only_for_followers.is_(False),
                    models.Post.is_private.is_(False),
                )
            )
            .join(
                models.post_hashtags_many_to_many,
                models.Post.uuid == models.post_hashtags_many_to_many.c.post_uuid,
            )
            .join(
                models.HashTag,
                models.HashTag.uuid == models.post_hashtags_many_to_many.c.hashtag_uuid,
            )
            .order_by(
                models.Post.created_at.desc(),
            )
        )

        result = await self.db_session.execute(select)
        items = [result.to_pydantic() for result in result.scalars().unique().all()]
        return items

    async def upsert_post_position_metadata(
        self, body: schemas.PostPositionMetadata
    ) -> schemas.PostPositionMetadata:
        result = await models.PostLayout.get(
            db_session=self.db_session,
            profile_uuid=body.profile_uuid,
        )
        if result:
            await result.update(
                db_session=self.db_session,
                **body.model_dump(exclude={"profile_uuid"}),
            )
        else:
            result = await models.PostLayout.create(
                db_session=self.db_session,
                **body.model_dump(),
            )
            if not result:
                raise HTTPException(status_code=500, detail="Failed to create post!")
        return result.to_pydantic()

    async def get_layout(self, profile_uuid: UUID) -> schemas.PostPositionMetadata:
        stmt = sa.select(models.PostLayout).where(
            models.PostLayout.profile_uuid == profile_uuid
        )
        result = await self.db_session.scalar(stmt)
        if not result:
            raise HTTPException(status_code=404, detail="Layout not found")
        return result.to_pydantic()

    async def view_post(
        self, logged_in_profile_uuid: UUID, viewer_uuid: UUID, post_uuid: UUID
    ) -> schemas.PostMetadata:
        _check_if_already_viewed = await self._check_if_already_viewed(
            post_uuid=post_uuid, viewer_uuid=viewer_uuid
        )
        if not _check_if_already_viewed:
            stmt = sa.insert(models.post_view_many_to_many).values(
                post_uuid=post_uuid, viewer_uuid=viewer_uuid
            )
            await self.db_session.execute(stmt)
            await self.db_session.commit()
            post = await models.Post.get(
                db_session=self.db_session,
                uuid=post_uuid,
            )
            if not post:
                raise HTTPException(status_code=404, detail="Profile not found!")
            if post:
                post.view_count += 1
                await self.db_session.commit()
                print(post.view_count)
            _check_if_already_viewed = True
        return await self.get_metadata(
            post_uuid=post_uuid,
            logged_in_profile_uuid=logged_in_profile_uuid,
            viewer_uuid=viewer_uuid,
        )

    async def _check_if_already_viewed(self, post_uuid: UUID, viewer_uuid: UUID):
        is_already_viewed_stmt = (
            sa.select(sa.func.count())
            .select_from(models.post_view_many_to_many)
            .where(
                models.post_view_many_to_many.c.post_uuid == post_uuid,
                models.post_view_many_to_many.c.viewer_uuid == viewer_uuid,
            )
        )
        count = await self.db_session.scalar(is_already_viewed_stmt)
        return count is not None and count > 0

    async def _get_view_count(self, db_session: AsyncSession, post_uuid: UUID):
        stmt = (
            sa.select(sa.func.count())
            .select_from(models.post_view_many_to_many)
            .where(
                models.post_view_many_to_many.c.post_uuid == post_uuid,
            )
        )
        result = await db_session.execute(stmt)
        return result.scalar()

    async def _get_like_count(self, db_session: AsyncSession, post_uuid: UUID):
        stmt = (
            sa.select(sa.func.count())
            .select_from(models.post_like_many_to_many)
            .where(
                models.post_like_many_to_many.c.post_uuid == post_uuid,
            )
        )
        result = await db_session.execute(stmt)
        return result.scalar()

    async def _check_if_already_liked_post(self, post_uuid: UUID, liker_uuid: UUID):
        is_already_liked_stmt = (
            sa.select(sa.func.count())
            .select_from(models.post_like_many_to_many)
            .where(
                models.post_like_many_to_many.c.post_uuid == post_uuid,
                models.post_like_many_to_many.c.liker_uuid == liker_uuid,
            )
        )
        count = await self.db_session.scalar(is_already_liked_stmt)
        return count is not None and count > 0

    async def get_metadata(
        self,
        post_uuid: UUID,
        logged_in_profile_uuid: UUID,
        viewer_uuid: UUID,
        has_already_viewed: bool | None = None,
        has_already_liked: bool | None = None,
    ) -> schemas.PostMetadata:
        post = await models.Post.get(db_session=self.db_session, uuid=post_uuid)
        view_count = await self._get_view_count(
            db_session=self.db_session, post_uuid=post_uuid
        )
        like_count = await self._get_like_count(
            db_session=self.db_session, post_uuid=post_uuid
        )
        _check_if_already_viewed = has_already_viewed
        if not _check_if_already_viewed:
            _check_if_already_viewed = await self._check_if_already_viewed(
                post_uuid=post_uuid, viewer_uuid=viewer_uuid
            )
        _check_if_already_liked_post = has_already_liked
        if not _check_if_already_liked_post:
            _check_if_already_liked_post = await self._check_if_already_liked_post(
                post_uuid=post_uuid, liker_uuid=viewer_uuid
            )
        if not post:
            raise HTTPException(
                status_code=400,
                detail="Post not found!",
            )

        return schemas.PostMetadata(
            has_already_viewed=_check_if_already_viewed or False,
            view_count=view_count or 0,
            has_already_liked=_check_if_already_liked_post or False,
            like_count=like_count or 0,
        )

    async def get_post_by_uuid(self, post_uuid: UUID) -> schemas.PostOut:
        post = await models.Post.get(
            db_session=self.db_session,
            uuid=post_uuid,
        )
        if not post:
            raise HTTPException(status_code=404, detail="Post not found!")

        return post.to_pydantic()

    async def like_unlike_post(
        self,
        post_uuid: UUID,
        logged_in_profile_uuid: UUID,
        liker_uuid: UUID,
    ) -> schemas.PostMetadata:
        _check_if_already_liked_post = await self._check_if_already_liked_post(
            post_uuid=post_uuid, liker_uuid=liker_uuid
        )
        if not _check_if_already_liked_post:
            stmt = sa.insert(models.post_like_many_to_many).values(
                post_uuid=post_uuid, liker_uuid=liker_uuid
            )
            await self.db_session.execute(stmt)
            await self.db_session.commit()
            post = await models.Post.get(
                db_session=self.db_session,
                uuid=post_uuid,
            )
            if not post:
                raise HTTPException(status_code=404, detail="Post not found!")
            liker_profile = await Profile.get(
                db_session=self.db_session, uuid=liker_uuid
            )

            if not liker_profile:
                raise HTTPException(status_code=404, detail="Profile not found!")
            if not post.profile_uuid == liker_profile.uuid:
                notification_body = NotificationBodySchema(
                    profile_uuid=str(liker_uuid),
                    notification_type=NotificationType.NEW_LIKE.value,
                    profile_image=str(liker_profile.avatar_media),
                    profile_name=str(liker_profile.account.username),
                    uuid=str(post.uuid),
                )
                notification_in = NotificationIn(
                    title="New Like",
                    body=f"{liker_profile.account.username} liked your Post!",
                    notification_type=NotificationType.NEW_LIKE.value,
                    profile_uuid=post.profile_uuid,
                    data=notification_body.model_dump(),
                )
                notification_out = await Notification.create(
                    db_session=self.db_session, **notification_in.model_dump()
                )
                if notification_out and not settings.debug:
                    await notification_out.send_multicast_notification(
                        profile_uuid_to_send_notification=post.profile_uuid,
                        db_session=self.db_session,
                    )
            _check_if_already_liked_post = True
        else:
            stmt = sa.delete(models.post_like_many_to_many).where(
                models.post_like_many_to_many.c.post_uuid == post_uuid,
                models.post_like_many_to_many.c.liker_uuid == liker_uuid,
            )
            await self.db_session.execute(stmt)
            await self.db_session.commit()
            _check_if_already_liked_post = False

        return await self.get_metadata(
            post_uuid=post_uuid,
            logged_in_profile_uuid=logged_in_profile_uuid,
            viewer_uuid=liker_uuid,
        )

    async def search_post(
        self,
        searcher_uuid: UUID,
        title: str,
        keywords: str,
        genre: core_schemas.HashTag | None,
        limit: int,
        offset: int,
    ) -> PaginatedResponse[schemas.PostOut]:
        # (check if post title contains title)
        stmt = (
            sa.select(models.Post)
            .where(
                models.Post.is_draft.is_(False),
                models.Post.is_membership_only.is_(False),
                models.Post.is_only_for_followers.is_(False),
                models.Post.is_private.is_(False),
            )
            .join(
                models.post_hashtags_many_to_many,
                models.Post.uuid == models.post_hashtags_many_to_many.c.post_uuid,
            )
            .join(
                models.HashTag,
                models.HashTag.uuid == models.post_hashtags_many_to_many.c.hashtag_uuid,
            )
        )

        # Apply search filters
        if title:
            stmt = stmt.where(
                models.Post.post_title.ilike(f"%{title}%"),
            )

        if keywords:
            stmt = stmt.where(
                sa.or_(
                    models.Post.post_title.ilike(f"%{keywords}%"),
                    models.Post.caption.ilike(f"%{keywords}%"),
                    models.Post.music_title.ilike(f"%{keywords}%"),
                )
            )

        if genre:
            if genre.uuid:
                sub_query = (
                    sa.select(models.Post.uuid)
                    .join(
                        models.post_hashtags_many_to_many,
                        models.Post.uuid
                        == models.post_hashtags_many_to_many.c.post_uuid,
                    )
                    .join(
                        models.HashTag,
                        models.HashTag.uuid
                        == models.post_hashtags_many_to_many.c.hashtag_uuid,
                    )
                )
                sub_query = sub_query.where(models.HashTag.uuid == genre.uuid)
                stmt = stmt.where(models.Post.uuid.in_(sub_query))

            # sub_query = sub_query.where(models.HashTag.name == genre.name)

        # Order by latest posts
        stmt = stmt.order_by(models.Post.created_at.desc())
        count_stmt = sa.select(sa.func.count()).select_from(stmt.subquery())
        total = await self.db_session.scalar(count_stmt)
        stmt = stmt.limit(limit).offset(offset)

        # Execute the query
        result = await self.db_session.execute(stmt)

        items = [result.to_pydantic() for result in result.scalars().unique().all()]
        return PaginatedResponse(
            limit=limit,
            offset=offset,
            items=items,
            total=total or 0,
        )

    async def search_all(
        self, searcher_uuid: UUID, keyword: str
    ) -> schemas.AllSearchResults:
        # TODO need to do permission check or may be reuse search func from own repos.
        keyword = keyword.lower()
        post_search_stmt = (
            sa.select(models.Post)
            .where(
                models.Post.post_title.ilike(f"%{keyword}%"),
                models.Post.is_private.is_(False),
            )
            .limit(10)
        ).order_by(models.Post.created_at.desc())
        posts = await self.db_session.scalars(post_search_stmt)
        gig_list_search_stmt = (
            sa.select(GigList).where(GigList.title.ilike(f"%{keyword}%")).limit(10)
        ).order_by(GigList.created_at.desc())
        gig_lists = await self.db_session.scalars(gig_list_search_stmt)
        profile_search_stmt = (
            sa.select(Profile)
            .join(Account, Profile.account_uuid == Account.uuid)
            .where(Account.username.ilike(f"%{keyword}%"))
            .limit(10)
        ).order_by(Profile.created_at.desc())
        profiles = await self.db_session.scalars(profile_search_stmt)
        return schemas.AllSearchResults(
            posts=[post.to_pydantic() for post in posts],
            profiles=[p.to_pydantic() for p in profiles],
            gig_list=[g.to_pydantic() for g in gig_lists],
        )

    async def get_all_self_post(self, profile_uuid: UUID):
        profile = await Profile.get(db_session=self.db_session, uuid=profile_uuid)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found!")
        stmt = sa.select(models.Post).where((models.Post.profile_uuid == profile_uuid))

        result = await self.db_session.execute(stmt)
        return [result.to_pydantic() for result in result.scalars().unique().all()]
