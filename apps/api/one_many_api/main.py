from contextlib import asynccontextmanager
from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException

from one_many_api.catalog_routes import catalog_router
from one_many_api.config import Settings
from one_many_api.database import build_session_factory
from one_many_api.discovery_routes import discovery_router
from one_many_api.funding_routes import funding_router
from one_many_api.ledger_routes import ledger_router
from one_many_api.logging import configure_logging
from one_many_api.reservation_routes import reservation_router
from one_many_api.routes import router


def create_app(settings: Settings | None = None) -> CORSMiddleware:
    settings = settings or Settings()
    logger = configure_logging(settings.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        connection = build_session_factory(settings)
        app.state.db_session_factory = connection[0] if connection else None
        logger.info("application_started")
        try:
            yield
        finally:
            if connection:
                connection[1].dispose()
            logger.info("application_stopped")

    app = FastAPI(title="ONE / MANY API", version="0.1.0", lifespan=lifespan)
    app.state.settings = settings
    app.include_router(router)
    app.include_router(discovery_router)
    app.include_router(catalog_router)
    app.include_router(funding_router)
    app.include_router(ledger_router)
    app.include_router(reservation_router)

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException) -> JSONResponse:
        message = HTTPStatus(exc.status_code).phrase
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": f"http_{exc.status_code}", "message": message}},
            headers=exc.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={"error": {"code": "validation_error", "message": "Request validation failed"}},
        )

    @app.exception_handler(Exception)
    async def unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        logger.error("unhandled_exception", extra={"error_type": type(exc).__name__})
        return JSONResponse(
            status_code=500,
            content={"error": {"code": "internal_error", "message": "Internal server error"}},
        )

    @app.middleware("http")
    async def response_hardening(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-Frame-Options"] = "DENY"
        if request.url.path.startswith("/api/v1/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.get("/api/v1/health", tags=["health"])
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": "one-many-api", "version": "0.1.0"}

    @app.get("/api/v1/ready", tags=["health"])
    def ready(request: Request) -> dict[str, str]:
        """Check actual database connectivity and applied Stage 6 migrations.

        Render must not route app traffic when database schema is absent.
        A healthy process with missing credentials or a disconnected database
        remains separately visible via /health.
        """
        factory = getattr(request.app.state, "db_session_factory", None)
        if factory is None:
            raise HTTPException(503, "Database is not configured")
        try:
            with factory() as db:
                db.execute(text("SELECT 1"))
                revision = db.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
                db.execute(text("SELECT 1 FROM funding_ledger_events LIMIT 1"))
            if revision != "20261112_06":
                raise HTTPException(503, "Database migrations are not current")
        except SQLAlchemyError:
            raise HTTPException(503, "Database is not ready") from None
        return {"status": "ready", "service": "one-many-api"}


    # Wrap the entire app so unexpected error responses also receive CORS headers.
    return CORSMiddleware(
        app,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
    )


app = create_app()
