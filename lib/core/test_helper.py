from datetime import time
from typing import List
from uuid import UUID

from faker import Faker
from features.accounts import models, schemas
from features.accounts.schemas import AccountOut, SignUp
from features.gig_list.schemas import GigListCreate, GigListOut
from features.profile import schemas as profile_schemas
from features.profile.models import Interest, MyServices, Skill
from features.profile.repo import ProfileRepoImpl
from features.profile.schemas import (
    AchievementIn,
    AvailabilityIn,
    ContactIn,
    EducationIn,
    ExperiencesIn,
    LocationIn,
    ProfileFewerDetailsOut,
    ProfileIn,
    ProfileMetaDataOut,
    ProfileOut,
    SocialLinkIn,
    SocialLinks,
)
from features.sup.schemas import SupCreate, SupCreatedFromEnum, SupOut
from httpx import AsyncClient

from core.jwt_authenticator import TokenOut
from core.response import PaginatedResponse, SimpleResponse
from core.schemas import HashTag

from .global_import import AsyncSession

faker = Faker()


async def generate_fake_profiles(db_session: AsyncSession, total: int = 10):
    email_set = set()
    interest = await Interest.create(
        db_session=db_session,
        **dict(name="test123", category="test123"),
    )
    skill = await Skill.create(
        db_session=db_session,
        **dict(name="HipHop", category="Music"),
    )
    service = await MyServices.create(
        db_session=db_session,
        **dict(name="HipHop", category="Rap"),
    )
    list_profile: List[ProfileOut] = []
    profile_repo = ProfileRepoImpl(db_session=db_session)
    for i in range(total):
        email = faker.unique.email()
        if email in email_set:
            continue
        account_create = SignUp(
            email=faker.unique.email(),
            username=faker.name(),
            password="Pa$$w0rd123",
            confirm_password="Pa$$w0rd123",
            date_of_birth=faker.date_of_birth(minimum_age=18, maximum_age=50),
        )
        account_created = await models.Account.register(
            db_session=db_session, body=account_create
        )
        email_set.add(account_created.email)

        location_in = LocationIn(
            address=faker.street_address(),
            country=faker.country(),
            city=faker.city(),
            state="",
        )
        social_links_in = SocialLinkIn(
            type=SocialLinks.facebook,
            url="https://facebook.com",
        )
        contact_in = ContactIn(
            type="email",
            value=email,
        )
        exp_in = ExperiencesIn(
            name="play guitar",
            category="guitar",
        )
        education = EducationIn(
            name="test",
            url="www.github.com",
        )
        achievement = AchievementIn(
            name="test",
            category="test",
            url="www.github.com",
        )
        profile_in = ProfileIn(
            account_uuid=account_created.uuid,
            cover_media="test.png",
            avatar_media="test.png",
            location=location_in,
            bio="test" * 50,
            availability_status=True,
            custom_phrase="test",
            closing_message="test",
            interests=[interest.uuid],  # type: ignore
            availability=[
                AvailabilityIn(day=3, start_time=time(8, 1), end_time=time(14, 1))
            ],
            contacts=[contact_in],
            experiences=[exp_in],
            skills=[skill.uuid],  # type: ignore
            educations=[education],
            social_links=[social_links_in],
            services=[service.uuid],  # type: ignore
            achievements=[achievement],
        )

        new_profile = await profile_repo.create_profile(body=profile_in)
        list_profile.append(new_profile)
    return list_profile


async def login(async_client: AsyncClient, email: str, password: str) -> TokenOut:
    body = schemas.SignIn(
        email=email,
        password=password,
    )
    response = await async_client.post(
        "/api/v1/accounts/sign-in", json=body.model_dump()
    )

    assert response.status_code == 200
    sign_in_success: schemas.SignInSuccess = schemas.SignInSuccess.model_validate(
        response.json()
    )
    assert sign_in_success

    # verify otp
    response = await async_client.post(
        "/api/v1/accounts/verify-otp",
        headers={"Authorization": f"Bearer {sign_in_success.session_token}"},
        json=schemas.VerifyOTP(email=body.email, otp="133733").model_dump(),
    )
    assert response.status_code == 200
    token = TokenOut.model_validate(response.json())
    assert token

    return token


async def get_profile(async_client: AsyncClient, token: TokenOut, create: bool = False):
    # get accounts
    response = await async_client.get(
        "/api/v1/accounts/me",
        headers={"Authorization": f"Bearer {token.access_token}"},
    )
    assert response.status_code == 200
    account = schemas.AccountOut.model_validate(response.json())
    if create:
        try:
            return await create_a_profile(async_client, token, account)
        except Exception:
            pass

    profile_response = await async_client.get(
        "/api/v1/profiles/",
        headers={"Authorization": f"Bearer {token.access_token}"},
        params={"account_uuid": str(account.uuid)},
    )
    assert profile_response.status_code == 200
    profile = profile_schemas.ProfileOut.model_validate(profile_response.json())
    assert profile
    return profile


async def login_and_get_profile(
    async_client: AsyncClient, email: str, password: str, create=False
):
    token = await login(async_client, email, password)
    return await get_profile(async_client, token, create=create), token


async def check_metadata(
    async_client: AsyncClient, token: TokenOut, profile_uuid: UUID
):
    # get accounts
    response = await async_client.get(
        f"/api/v1/profiles/{str(profile_uuid)}/metadata/",
        headers={"Authorization": f"Bearer {token.access_token}"},
    )
    assert response.status_code == 200
    metadata = ProfileMetaDataOut.model_validate(response.json())

    assert metadata

    return metadata


async def create_a_profile(
    async_client: AsyncClient, token: TokenOut, account: AccountOut
):
    # Get one skill UUID
    response = await async_client.get(
        "/api/v1/profiles/skills",
        headers={"Authorization": f"Bearer {token.access_token}"},
    )
    assert response.status_code == 200

    skills = response.json()
    assert skills
    skill = profile_schemas.SkillOut.model_validate(skills[0])
    skill_uuid = skill.uuid
    assert skill_uuid

    # Get one interest UUID
    response = await async_client.get(
        "/api/v1/profiles/interests",
        headers={"Authorization": f"Bearer {token.access_token}"},
    )
    assert response.status_code == 200

    interests = response.json()
    assert interests
    interest = profile_schemas.InterestOut.model_validate(interests[0])
    interest_uuid = interest.uuid
    assert interest_uuid

    profile = profile_schemas.ProfileIn(
        bio="hello world",
        custom_phrase="hello world",
        closing_message="hello world",
        cover_media="https://gigger.sgp1.cdn.digitaloceanspaces.com/cover.png",
        avatar_media="https://gigger.sgp1.cdn.digitaloceanspaces.com/avatar.png",
        account_uuid=account.uuid,
        interests=[interest_uuid],
        skills=[skill_uuid],
        services=[],
        location=profile_schemas.LocationIn(
            country="us",
            city="newyork",
            state="ny",
            address="1234 abc st",
        ),
        experiences=[
            profile_schemas.ExperiencesIn(
                name="play guitar",
                category="guitar",
            )
        ],
        educations=[
            profile_schemas.EducationIn(
                name="university of abc",
                url="https://www.abc.edu",
            )
        ],
        availability_status=True,
        availability=[
            profile_schemas.AvailabilityIn(
                start_time=time(9, 0),
                end_time=time(17, 0),
                day=1,
            )
        ],
        contacts=[
            profile_schemas.ContactIn(
                type="email",
                value="lHqgZ@example.com",
            )
        ],
        social_links=[
            profile_schemas.SocialLinkIn(
                type=profile_schemas.SocialLinks.facebook,
                url="https://facebook.com",
            ),
        ],
        achievements=[
            profile_schemas.AchievementIn(
                name="hello world",
                category="hello world",
                url="https://gigger.sgp1.cdn.digitaloceanspaces.com/cover.png",
            ),
            profile_schemas.AchievementIn(
                name="hello world",
                category="hello world",
                url="https://gigger.sgp1.cdn.digitaloceanspaces.com/cover.png",
            ),  # duplicate achievement should be ignored
        ],
    )

    response = await async_client.post(
        "/api/v1/profiles/",
        headers={"Authorization": f"Bearer {token.access_token}"},
        json=profile.model_dump(mode="json"),
    )
    assert response.status_code == 200
    profile = profile_schemas.ProfileOut.model_validate(response.json())

    assert profile
    return profile


async def check_follower_requests(
    async_client: AsyncClient, token: TokenOut, profile_uuid: UUID
):
    response = await async_client.get(
        f"/api/v1/profiles/{str(profile_uuid)}/followers/requests/",
        headers={"Authorization": f"Bearer {token.access_token}"},
    )
    assert response.status_code == 200
    return PaginatedResponse[ProfileFewerDetailsOut].model_validate(response.json())


async def accept_follower_requests(
    async_client: AsyncClient,
    token: TokenOut,
    profile_uuid: UUID,  # to_accept
    to_accept: UUID,
):
    response = await async_client.post(
        f"/api/v1/profiles/{str(profile_uuid)}/followers/accept/",
        params={"to_accept": str(to_accept)},
        headers={"Authorization": f"Bearer {token.access_token}"},
    )
    assert response.status_code == 200
    return SimpleResponse.model_validate(response.json())


async def reject_follower_requests(
    async_client: AsyncClient,
    token: TokenOut,
    profile_uuid: UUID,
    rejecter: UUID,
):
    response = await async_client.post(
        f"/api/v1/profiles/{str(profile_uuid)}/followers/reject/",
        params={"rejecter": str(rejecter)},
        headers={"Authorization": f"Bearer {token.access_token}"},
    )
    assert response.status_code == 200
    return SimpleResponse.model_validate(response.json())


async def list_followers(
    async_client: AsyncClient, token: TokenOut, profile_uuid: UUID
):
    response = await async_client.get(
        f"/api/v1/profiles/{str(profile_uuid)}/followers/",
        headers={"Authorization": f"Bearer {token.access_token}"},
    )
    assert response.status_code == 200
    return PaginatedResponse[ProfileFewerDetailsOut].model_validate(response.json())


async def list_following(
    async_client: AsyncClient, token: TokenOut, profile_uuid: UUID
):
    response = await async_client.get(
        f"/api/v1/profiles/{str(profile_uuid)}/following/",
        headers={"Authorization": f"Bearer {token.access_token}"},
    )
    assert response.status_code == 200
    return PaginatedResponse[ProfileFewerDetailsOut].model_validate(response.json())


async def unfollow(
    async_client: AsyncClient, token: TokenOut, profile_uuid: UUID, to_unfollow: UUID
):
    response = await async_client.delete(
        f"/api/v1/profiles/{str(profile_uuid)}/followers/unfollow/",
        params={"to_unfollow": str(to_unfollow)},
        headers={"Authorization": f"Bearer {token.access_token}"},
    )
    assert response.status_code == 200
    return SimpleResponse.model_validate(response.json())


async def check_pending_requests(
    async_client: AsyncClient, token: TokenOut, profile_uuid: UUID
):
    response = await async_client.get(
        f"/api/v1/profiles/{str(profile_uuid)}/following/requests/",
        headers={"Authorization": f"Bearer {token.access_token}"},
    )
    assert response.status_code == 200
    return PaginatedResponse[ProfileFewerDetailsOut].model_validate(response.json())


async def cancel_pending_requests(
    async_client: AsyncClient,
    token: TokenOut,
    profile_uuid: UUID,
    rejecter: UUID,
):
    response = await async_client.delete(
        url=f"/api/v1/profiles/{str(profile_uuid)}/followers/cancel-pending/",
        params={"rejecter": str(rejecter)},
        headers={"Authorization": f"Bearer {token.access_token}"},
    )
    assert response.status_code == 200
    return SimpleResponse.model_validate(response.json())


async def create_gig_list(
    async_client: AsyncClient,
    token: TokenOut,
    gig_list_data: GigListCreate,
):
    response = await async_client.post(
        url="/api/v1/gig-list/",
        json=gig_list_data.model_dump(mode="json"),
        headers={"Authorization": f"Bearer {token.access_token}"},
    )
    assert response.status_code == 200 or response.status_code == 201
    return GigListOut.model_validate(response.json())


async def list_gig_list_by_profile(
    async_client: AsyncClient,
    token: TokenOut,
    profile_uuid: UUID,
):
    response = await async_client.get(
        url=f"/api/v1/gig-list/{profile_uuid}/",
        headers={"Authorization": f"Bearer {token.access_token}"},
    )
    assert response.status_code == 200, (
        f"Unexpected status code: {response.status_code}"
    )
    return [GigListOut.model_validate(item) for item in response.json()]


async def list_recommended_artists(
    async_client: AsyncClient, token: TokenOut, profile_uuid: UUID
) -> PaginatedResponse[ProfileOut]:
    response = await async_client.get(
        f"/api/v1/profiles/{str(profile_uuid)}/recommended-artist/",
        headers={"Authorization": f"Bearer {token.access_token}"},
    )
    assert response.status_code == 200, (
        f"Unexpected status code: {response.status_code}"
    )

    return PaginatedResponse[ProfileOut].model_validate(response.json())


async def create_sups_and_get(
    async_client: AsyncClient, token: TokenOut, profile_uuid: UUID
):
    body = SupCreate(
        caption="hello world",
        profile_uuid=profile_uuid,
        thumbnail_url="https://gigger.sgp1.cdn.digitaloceanspaces.com/cover.png",
        video_url="https://gigger.sgp1.cdn.digitaloceanspaces.com/cover.png",
        is_membership_only=False,
        is_only_for_followers=False,
        location="hello world",
        tagged_profiles=[],
        hashtags=[
            HashTag(name="hello sup", uuid=None),
        ],
        create_from=SupCreatedFromEnum.NONE,
    )

    response = await async_client.post(
        "/api/v1/sup/",
        headers={"Authorization": f"Bearer {token.access_token}"},
        json=body.model_dump(mode="json"),
    )
    assert response.status_code == 200
    sup = SupOut.model_validate(response.json())
    assert sup
    assert sup.caption == body.caption
    assert sup.video_url == body.video_url
    assert sup.thumbnail_url == body.thumbnail_url
    assert sup.is_membership_only == body.is_membership_only
    assert sup.is_only_for_followers == body.is_only_for_followers
    assert sup.location == body.location
    assert len(sup.tagged_profiles) == 0
    # assert len(sup.hashtags) == 1
    # assert sup.hashtags[0].name == body.hashtags[0].name
    assert sup.create_from == body.create_from

    body2 = SupCreate(
        caption="POST",
        profile_uuid=profile_uuid,
        thumbnail_url="https://gigger.sgp1.cdn.digitaloceanspaces.com/cover.png",
        video_url="https://gigger.sgp1.cdn.digitaloceanspaces.com/cover.png",
        is_membership_only=False,
        is_only_for_followers=False,
        location="hello world",
        tagged_profiles=[],
        hashtags=[
            HashTag(name="hello sup", uuid=None),
        ],
        create_from=SupCreatedFromEnum.POST,
    )

    response2 = await async_client.post(
        "/api/v1/sup/",
        headers={"Authorization": f"Bearer {token.access_token}"},
        json=body2.model_dump(mode="json"),
    )
    assert response2.status_code == 200
    sup2 = SupOut.model_validate(response2.json())
    assert sup2
    assert sup2.caption == body2.caption
    assert sup2.video_url == body2.video_url
    assert sup2.thumbnail_url == body2.thumbnail_url
    assert sup2.is_membership_only == body2.is_membership_only
    assert sup2.is_only_for_followers == body2.is_only_for_followers
    assert sup2.location == body2.location
    assert len(sup2.tagged_profiles) == 0
    # assert len(sup2.hashtags) == 1
    # assert sup2.hashtags[0].name == body2.hashtags[0].name
    assert sup2.create_from == body2.create_from

    body3 = SupCreate(
        caption="GIG_LIST",
        profile_uuid=profile_uuid,
        thumbnail_url="https://gigger.sgp1.cdn.digitaloceanspaces.com/cover.png",
        video_url="https://gigger.sgp1.cdn.digitaloceanspaces.com/cover.png",
        is_membership_only=False,
        is_only_for_followers=False,
        location="hello world",
        tagged_profiles=[],
        hashtags=[
            HashTag(name="hello sup", uuid=None),
        ],
        create_from=SupCreatedFromEnum.GIG_LIST,
    )

    response3 = await async_client.post(
        "/api/v1/sup/",
        headers={"Authorization": f"Bearer {token.access_token}"},
        json=body3.model_dump(mode="json"),
    )
    assert response3.status_code == 200
    sup3 = SupOut.model_validate(response3.json())
    assert sup3
    assert sup3.caption == body3.caption
    assert sup3.video_url == body3.video_url
    assert sup3.thumbnail_url == body3.thumbnail_url
    assert sup3.is_membership_only == body3.is_membership_only
    assert sup3.is_only_for_followers == body3.is_only_for_followers
    assert sup3.location == body3.location
    assert len(sup3.tagged_profiles) == 0
    # assert len(sup3.hashtags) == 1
    # assert sup3.hashtags[0].name == body3.hashtags[0].name
    assert sup3.create_from == body3.create_from

    body4 = SupCreate(
        caption="ARTIST",
        profile_uuid=profile_uuid,
        thumbnail_url="https://gigger.sgp1.cdn.digitaloceanspaces.com/cover.png",
        video_url="https://gigger.sgp1.cdn.digitaloceanspaces.com/cover.png",
        is_membership_only=False,
        is_only_for_followers=False,
        location="hello world",
        tagged_profiles=[],
        hashtags=[
            HashTag(name="hello sup", uuid=None),
        ],
        create_from=SupCreatedFromEnum.ARTIST,
    )

    response4 = await async_client.post(
        "/api/v1/sup/",
        headers={"Authorization": f"Bearer {token.access_token}"},
        json=body4.model_dump(mode="json"),
    )
    assert response4.status_code == 200
    sup4 = SupOut.model_validate(response4.json())
    assert sup4
    assert sup4.caption == body4.caption
    assert sup4.video_url == body4.video_url
    assert sup4.thumbnail_url == body4.thumbnail_url
    assert sup4.is_membership_only == body4.is_membership_only
    assert sup4.is_only_for_followers == body4.is_only_for_followers
    assert sup4.location == body4.location
    assert len(sup4.tagged_profiles) == 0
    # assert len(sup4.hashtags) == 1
    # assert sup4.hashtags[0].name == body4.hashtags[0].name
    assert sup4.create_from == body4.create_from

    get_response = await async_client.get(
        f"/api/v1/sup/{profile_uuid}/",
        params={"created_from": SupCreatedFromEnum.NONE.value},
        headers={"Authorization": f"Bearer {token.access_token}"},
    )
    assert get_response.status_code == 200
    assert get_response.json()
    print(get_response.json())

    sups = [SupOut.model_validate(sup) for sup in get_response.json()]
    assert sups
    assert len(sups) == 4

    get_response = await async_client.get(
        f"/api/v1/sup/{profile_uuid}/",
        params={"created_from": SupCreatedFromEnum.POST.value},
        headers={"Authorization": f"Bearer {token.access_token}"},
    )
    assert get_response.status_code == 200
    assert get_response.json()

    sups = [SupOut.model_validate(sup) for sup in get_response.json()]
    assert sups
    assert len(sups) == 1
    for sup in sups:
        assert sup.create_from == SupCreatedFromEnum.POST

    get_response = await async_client.get(
        f"/api/v1/sup/{profile_uuid}/",
        params={"created_from": SupCreatedFromEnum.GIG_LIST.value},
        headers={"Authorization": f"Bearer {token.access_token}"},
    )
    assert get_response.status_code == 200
    assert get_response.json()

    sups = [SupOut.model_validate(sup) for sup in get_response.json()]
    assert sups
    assert len(sups) == 1
    for sup in sups:
        assert sup.create_from == SupCreatedFromEnum.GIG_LIST

    get_response = await async_client.get(
        f"/api/v1/sup/{profile_uuid}/",
        params={"created_from": SupCreatedFromEnum.ARTIST.value},
        headers={"Authorization": f"Bearer {token.access_token}"},
    )
    assert get_response.status_code == 200
    assert get_response.json()

    sups = [SupOut.model_validate(sup) for sup in get_response.json()]
    assert sups
    assert len(sups) == 1
    for sup in sups:
        assert sup.create_from == SupCreatedFromEnum.ARTIST

    list_profile_having_sup_none = await list_profile_having_sup(
        async_client=async_client,
        token=token,
        profile_uuid=profile_uuid,
        created_from=SupCreatedFromEnum.NONE,
    )
    assert list_profile_having_sup_none
    assert list_profile_having_sup_none.total == 1  # only one profile

    # TODO: test other created_from


async def list_profile_having_sup(
    async_client: AsyncClient,
    token: TokenOut,
    profile_uuid: UUID,
    created_from: SupCreatedFromEnum = SupCreatedFromEnum.NONE,
):
    response = await async_client.get(
        "/api/v1/sup/",
        headers={"Authorization": f"Bearer {token.access_token}"},
        params={"created_from": created_from.value, "limit": 100, "offset": 0},
    )
    assert response.status_code == 200
    return PaginatedResponse[ProfileFewerDetailsOut].model_validate(response.json())
