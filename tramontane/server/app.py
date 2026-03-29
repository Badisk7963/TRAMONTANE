"""Tramontane FastAPI application factory.

EU Premium from first byte — proper HTTP status codes for GDPR,
budget, and loop errors. SSE streaming for all pipeline output.
"""

from __future__ import annotations

import logging
import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

import tramontane
from tramontane.core.exceptions import (
    AgentTimeoutError,
    BudgetExceededError,
    GDPRViolationError,
    HandoffLoopError,
    PipelineValidationError,
    TramontaneError,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Custom middleware
# ---------------------------------------------------------------------------


class TramontaneHeaderMiddleware(BaseHTTPMiddleware):
    """Inject Tramontane + EU sovereignty headers on every response."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint,
    ) -> Response:
        """Add X-Tramontane-Version and X-EU-Sovereign headers."""
        response = await call_next(request)
        response.headers["X-Tramontane-Version"] = tramontane.__version__
        response.headers["X-EU-Sovereign"] = "true"
        return response


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------


def create_app(
    multitenancy: bool = False,
    db_path: str = "tramontane.db",
) -> FastAPI:
    """Create and configure the Tramontane FastAPI application."""
    app = FastAPI(
        title="TRAMONTANE",
        description="Mistral-native agent orchestration API",
        version=tramontane.__version__,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # -- State -------------------------------------------------------------
    app.state.db_path = db_path
    app.state.multitenancy = multitenancy

    # -- CORS --------------------------------------------------------------
    allowed_origins = os.environ.get(
        "TRAMONTANE_ALLOWED_ORIGINS", "*"
    ).split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # -- Custom headers ----------------------------------------------------
    app.add_middleware(TramontaneHeaderMiddleware)

    # -- Exception handlers ------------------------------------------------

    @app.exception_handler(BudgetExceededError)
    async def budget_handler(
        _request: Request, exc: BudgetExceededError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=402,
            content={
                "error": "BudgetExceededError",
                "detail": str(exc),
                "code": 402,
            },
        )

    @app.exception_handler(PipelineValidationError)
    async def validation_handler(
        _request: Request, exc: PipelineValidationError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "error": "PipelineValidationError",
                "detail": str(exc),
                "code": 422,
            },
        )

    @app.exception_handler(HandoffLoopError)
    async def loop_handler(
        _request: Request, exc: HandoffLoopError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=508,
            content={
                "error": "HandoffLoopError",
                "detail": str(exc),
                "code": 508,
            },
        )

    @app.exception_handler(AgentTimeoutError)
    async def timeout_handler(
        _request: Request, exc: AgentTimeoutError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=504,
            content={
                "error": "AgentTimeoutError",
                "detail": str(exc),
                "code": 504,
            },
        )

    @app.exception_handler(GDPRViolationError)
    async def gdpr_handler(
        _request: Request, exc: GDPRViolationError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=451,
            content={
                "error": "GDPRViolationError",
                "detail": str(exc),
                "code": 451,
            },
        )

    @app.exception_handler(TramontaneError)
    async def generic_handler(
        _request: Request, exc: TramontaneError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={
                "error": type(exc).__name__,
                "detail": str(exc),
                "code": 500,
            },
        )

    # -- Startup -----------------------------------------------------------

    @app.on_event("startup")
    async def startup() -> None:
        from tramontane.memory.longterm import LongTermMemory

        mem = LongTermMemory(db_path=db_path)
        mem._get_db()
        logger.info(
            "Tramontane API v%s ready — db=%s multitenancy=%s",
            tramontane.__version__, db_path, multitenancy,
        )

    # -- Mount routers -----------------------------------------------------
    from tramontane.server.routes import router as api_router

    app.include_router(api_router)

    return app
