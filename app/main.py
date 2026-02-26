import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import init_db
from app.routers import health, messenger, instagram, email as email_router

logging.basicConfig(
    level=logging.INFO,
    format='{"time": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}',
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up — initialising database tables")
    await init_db()
    logger.info("Database ready")
    yield
    logger.info("Shutting down")


app = FastAPI(
    title="AI Customer Service Agent",
    version="1.0.0",
    description="Handles Messenger, Instagram, and Email inquiries via RAG + LLM.",
    lifespan=lifespan,
)

app.include_router(health.router, tags=["health"])
app.include_router(messenger.router, tags=["messenger"])
app.include_router(instagram.router, tags=["instagram"])
app.include_router(email_router.router, tags=["email"])
