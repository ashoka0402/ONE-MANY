from contextlib import asynccontextmanager
from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from one_many_api.catalog_routes import catalog_router
from one_many_api.config import Settings
from one_many_api.database import build_session_factory
from one_many_api.discovery_routes import discovery_router
from one_many_api.funding_routes import funding_router
from one_many_api.logging import configure_logging
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

    @app.get("/api/v1/health", tags=["health"])
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": "one-many-api", "version": "0.1.0"}

    # Wrap the entire app so unexpected error responses also receive CORS headers.
    return CORSMiddleware(
        app,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH", "DELETE"],
        allow_headers=["Content-Type", "Authorization"],
    )


app = create_app()
