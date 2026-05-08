"""FastAPI application factory."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).resolve().parent / "static"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    database_url: str = "postgresql://medrag:medrag@localhost:5432/medrag"
    redis_url: str = "redis://localhost:6379/0"

    pinecone_api_key: str = "mock-dev"
    pinecone_index: str = "medrag"
    pinecone_namespace: str = "__default__"
    pinecone_text_field: str = "text"

    anthropic_api_key: str = "mock-dev"
    openai_api_key: str = "mock-dev"
    openai_model: str = "gpt-4o-mini"
    llm_provider: str = "openai"

    jwt_secret_key: str = "dev-secret-key-32-chars-minimum-long"
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 30

    environment: str = "development"
    log_level: str = "INFO"


settings = Settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.basicConfig(
        level=settings.log_level.upper(),
        format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
    )
    from app.services import is_mock_mode

    logger.info(
        "MedRAG starting (env=%s, llm=%s, mode=%s)",
        settings.environment,
        settings.llm_provider,
        "mock" if is_mock_mode() else "production",
    )
    yield
    logger.info("MedRAG shutting down")


def create_app() -> FastAPI:
    app = FastAPI(
        title="MedRAG",
        description="Hosted Retrieval-Augmented Generation service with an MCP server interface.",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    from app.mcp_server import mcp_app, mcp_router
    from app.routers.demo import router as demo_router

    app.include_router(demo_router)
    app.include_router(mcp_router)

    if mcp_app is not None:
        app.mount("/mcp", mcp_app)
        logger.info("MCP streamable-http server mounted at /mcp")
    else:
        logger.warning("`mcp` SDK not installed; only /mcp/info stub is available")

    if STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

        @app.get("/", response_class=HTMLResponse, include_in_schema=False)
        async def landing_page() -> HTMLResponse:
            index = STATIC_DIR / "index.html"
            if index.exists():
                return HTMLResponse(index.read_text(encoding="utf-8"))
            return HTMLResponse("<h1>MedRAG</h1>", status_code=200)

    @app.get("/health", tags=["meta"])
    async def health_check() -> dict:
        from app.services import is_mock_mode

        return {
            "status": "ok",
            "mode": "mock" if is_mock_mode() else "production",
            "environment": settings.environment,
            "llm_provider": settings.llm_provider,
        }

    return app


app = create_app()
