from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import router
from app.api.middleware.error_handler import GlobalErrorHandlerMiddleware
from app.api.middleware.tracing import RequestTracingMiddleware
from app.database.metadata.session import get_async_session
from app.database.registry.database_registry import DatabaseRegistry


app = FastAPI(title="Capstone Project")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup/shutdown lifecycle.

    Startup:
    - ensure app DB sessionmaker can be created
    - load active datasource handles into DatabaseRegistry

    Shutdown:
    - best-effort close connector pools for loaded handles
    """
    sessionmaker = get_async_session()
    registry = DatabaseRegistry.get_instance()

    async with sessionmaker() as session:
        await registry.load_from_appdb(session)

    yield

    for handle in registry.list_all():
        try:
            await handle.connector.close()
        except Exception:
            # Best-effort shutdown; do not crash app shutdown
            pass


def create_app() -> FastAPI:
    app = FastAPI(
        title="Capstone Project",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Middleware order matters. Add minimal stack first.
    app.add_middleware(RequestTracingMiddleware)
    app.add_middleware(GlobalErrorHandlerMiddleware)

    app.include_router(router)

    return app


app = create_app()
