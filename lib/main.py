import contextlib
import os

import sentry_sdk
from core.config import settings
from core.dependencies import db_session_manager, get_db_session
from core.fileupload import file_upload_route
from core.global_import import AsyncSession
from fastapi import Depends, FastAPI
from features.accounts.api_view import account_router
from features.events.api_view import event_router
from features.gig_list.api_view import gig_list_router
from features.post.api_view import post_router
from features.profile.api_view import profile_router
from features.settings.api_view import setting_router
from features.sup.api_view import sup_router
from firebase_admin import credentials, initialize_app
from sqlalchemy import text


# logging.basicConfig()'
# logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
def init_firebase():
    try:
        lib_path = os.path.dirname(os.path.abspath(__file__))  # Path to `lib`
        json_path = os.path.join(lib_path, "gigger-google-service.json")
        cred = credentials.Certificate(json_path)
        initialize_app(cred)
    except Exception as e:
        raise e


if not settings.debug:
    sentry_sdk.init(
        dsn="https://9220556f982f4de72a424ef46ebaf284@o4508759038230528.ingest.us.sentry.io/4508759041966080",
        # Add data like request headers and IP for users,
        # see https://docs.sentry.io/platforms/python/data-management/data-collected/ for more info
        send_default_pii=True,
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for tracing.
        traces_sample_rate=1.0,
        _experiments={
            # Set continuous_profiling_auto_start to True
            # to automatically start the profiler on when
            # possible.
            "continuous_profiling_auto_start": True,
        },
    )


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    init_firebase()
    # TODO: improve lifespan type
    yield
    await db_session_manager.close()


fast_api_app = FastAPI(
    debug=settings.debug,
    docs_url="/gigger/docs",
    title="GiggerAPI",
    redoc_url=None,
    lifespan=lifespan,
)
fast_api_app.include_router(account_router)
fast_api_app.include_router(file_upload_route)

fast_api_app.include_router(setting_router)
fast_api_app.include_router(profile_router)
fast_api_app.include_router(post_router)
fast_api_app.include_router(sup_router)
fast_api_app.include_router(gig_list_router)
fast_api_app.include_router(event_router)


@fast_api_app.get("/", include_in_schema=False)
async def db_session(db_session: AsyncSession = Depends(get_db_session)):
    stmt = text("SELECT 'success!'")
    try:
        result = await db_session.execute(stmt)
        return {"detail": f"{result.scalar()}"}
    except Exception as _:
        return {"detail": "failed!"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:fast_api_app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
