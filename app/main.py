from __future__ import annotations
import asyncio
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi_limiter import FastAPILimiter

from .core.config import get_settings
from .core.exceptions import register_exception_handlers
from .core.logging_config import configure_logging, get_logger
from .middlewares.correlation import CorrelationIdMiddleware
from .middlewares.jwt_auth import JWTAuthenticationMiddleware
from .middlewares.logging import RequestLoggingMiddleware
from .routers import api_router
from .services.cache import redis_cache
from .services.database import mysql as mysql_service
from .services.messaging import connection as rabbitmq_connection
from .services.search import opensearch_client
from .services.secrets.aws_secrets import load_secrets_into_env

load_dotenv(".env", override=False)

settings = get_settings()
configure_logging(settings.log_level, settings.pii_fields_list)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global settings

    try:
        secrets = load_secrets_into_env(settings)
    except Exception as exc:  # pragma: no cover - best effort
        logger.warning("Failed to load AWS secrets", extra={"error": str(exc)})
        secrets = {}
    else:
        if secrets:
            get_settings.cache_clear()
            settings = get_settings()
            configure_logging(settings.log_level, settings.pii_fields_list)

    # Log status of dependent services before attempting initialization
    await log_dependency_status(settings)

    # Initialize services gracefully - each service handles its own connection errors
    await mysql_service.init_engine(settings)
    await redis_cache.init_cache(settings)
    await opensearch_client.init_client(settings)
    await rabbitmq_connection.init_connection(settings)
    
    # Initialize rate limiter only if Redis is available
    try:
        redis_client = redis_cache.get_client()
        await FastAPILimiter.init(redis_client)
    except RuntimeError:
        logger.warning("Rate limiting disabled - Redis connection unavailable")

    logger.info("Application startup complete")
    yield

    # Gracefully shutdown services (handles None cases)
    try:
        await mysql_service.shutdown_engine()
    except Exception as exc:
        logger.warning("Error shutting down MySQL", extra={"error": str(exc)})
    
    try:
        await redis_cache.close_cache()
    except Exception as exc:
        logger.warning("Error closing Redis cache", extra={"error": str(exc)})
    
    try:
        await opensearch_client.close_client()
    except Exception as exc:
        logger.warning("Error closing OpenSearch client", extra={"error": str(exc)})
    
    try:
        await rabbitmq_connection.close_connection()
    except Exception as exc:
        logger.warning("Error closing RabbitMQ connection", extra={"error": str(exc)})
    
    logger.info("Application shutdown complete")


app = FastAPI(title=settings.app_name, lifespan=lifespan)

register_exception_handlers(app, settings.pii_fields_list)

# Middleware order matters: Last added runs FIRST in request flow
# Add CorrelationIdMiddleware LAST so it runs FIRST and sets correlation ID before any other middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(JWTAuthenticationMiddleware, exempt_paths=settings.auth_exempt_paths_list)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(CorrelationIdMiddleware)  # Added LAST so it runs FIRST - sets correlation ID before auth/logging

app.include_router(api_router)


def custom_openapi() -> dict:
    """Attach JWT bearer security scheme to the OpenAPI schema so Swagger UI can accept tokens."""
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version="1.0.0",
        description="FastAPI microservice with JWT authentication and distributed dependencies.",
        routes=app.routes,
    )

    security_scheme = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Paste the JWT generated via scripts/generate_jwt.py",
        }
    }

    openapi_schema.setdefault("components", {}).setdefault("securitySchemes", {}).update(security_scheme)

    # Apply JWT security requirement to every path/method
    for methods in openapi_schema.get("paths", {}).values():
        for operation in methods.values():
            operation.setdefault("security", [{"BearerAuth": []}])

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


async def log_dependency_status(current_settings):
    """Check if dependent services are reachable and log their status."""
    dependency_checks = [
        mysql_service.check_status(current_settings),
        redis_cache.check_status(current_settings),
        opensearch_client.check_status(current_settings),
        rabbitmq_connection.check_status(current_settings),
    ]

    await asyncio.gather(*dependency_checks, return_exceptions=True)


