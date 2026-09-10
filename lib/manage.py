import asyncio
import csv
from datetime import date
from functools import wraps

import typer
from core.dependencies import get_db_session
from features.accounts import models as profile_models
from features.accounts import schemas as account_schemas
from features.profile import models, schemas

app = typer.Typer()


def coro(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))  # type: ignore

    return wrapper


@app.command("upload_interests")
@coro
async def upload_interests():
    """read interests csv file and upload to db."""
    async for session in get_db_session():
        count = 0
        with open("datas/interests.csv", "r", newline="") as f:
            csv_data = csv.reader(f)
            list_processed_data_name = []
            for row in csv_data:
                if row[0] in list_processed_data_name:
                    continue
                if len(row) != 2:
                    continue

                try:
                    count += 1
                    skill = schemas.SkillIn(name=row[0], category=row[1])
                    await models.Skill.create_if_not_exist(
                        db_session=session, **skill.model_dump()
                    )
                    my_service = schemas.MyServicesIn(name=row[0], category=row[1])
                    await models.MyServices.create_if_not_exist(
                        db_session=session, **my_service.model_dump()
                    )

                    interest = schemas.Interest(name=row[0], category=row[1])
                    await models.Interest.create_if_not_exist(
                        db_session=session, **interest.model_dump()
                    )
                    list_processed_data_name.append(row[0])

                except Exception:
                    pass
                    print(count)

            await session.close()


@app.command("add_dev_account")
@coro
async def add_dev_account():
    async for session in get_db_session():
        accounts = [
            account_schemas.SignUp(
                username="dev_1337",
                email="dev@gigger.art",
                password="Pa$$w0rd23",
                confirm_password="Pa$$w0rd23",
                date_of_birth=date(2000, 1, 1),
            ),
            account_schemas.SignUp(
                username="dev_1_1337",
                email="dev_1@gigger.art",
                password="Pa$$w0rd23",
                confirm_password="Pa$$w0rd23",
                date_of_birth=date(2000, 1, 1),
            ),
            account_schemas.SignUp(
                username="dev_2_1337",
                email="dev_2@gigger.art",
                password="Pa$$w0rd23",
                confirm_password="Pa$$w0rd23",
                date_of_birth=date(2000, 1, 1),
            ),
            account_schemas.SignUp(
                username="dev_3_1337",
                email="dev_3@gigger.art",
                password="Pa$$w0rd23",
                confirm_password="Pa$$w0rd23",
                date_of_birth=date(2000, 1, 1),
            ),
            account_schemas.SignUp(
                username="dev_4_1337",
                email="dev_4@gigger.art",
                password="Pa$$w0rd23",
                confirm_password="Pa$$w0rd23",
                date_of_birth=date(2000, 1, 1),
            ),
            account_schemas.SignUp(
                username="dev_5_1337",
                email="dev_5@gigger.art",
                password="Pa$$w0rd23",
                confirm_password="Pa$$w0rd23",
                date_of_birth=date(2000, 1, 1),
            ),
            account_schemas.SignUp(
                username="dev_6_1337",
                email="dev_6@gigger.art",
                password="Pa$$w0rd23",
                confirm_password="Pa$$w0rd23",
                date_of_birth=date(2000, 1, 1),
            ),
        ]
        for i in range(len(accounts)):
            account_body = accounts[i]
            account = await profile_models.Account.register(
                db_session=session, body=account_body
            )

            await account.update(
                db_session=session, is_active=True, email_verified=True
            )
            body = account_schemas.EmailVerificationInDev(
                opt="133733",
                email=account.email,
                account_uuid=account.uuid,
                dev_mode=True,
            )
            await profile_models.EmailVerification.create(
                db_session=session, **body.model_dump()
            )
        await session.close()


if __name__ == "__main__":
    app()
