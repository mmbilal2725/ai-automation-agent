"""
Shared pytest fixtures.
Env vars for testing are set here so no real .env is needed.
"""
import os
import pytest

# Set test env before any app imports
os.environ.setdefault("OPENAI_API_KEY", "sk-test-key")
os.environ.setdefault("META_APP_SECRET", "test_app_secret")
os.environ.setdefault("META_PAGE_ACCESS_TOKEN", "test_page_token")
os.environ.setdefault("META_VERIFY_TOKEN", "test_verify_token")
os.environ.setdefault("SENDGRID_API_KEY", "SG.test")
os.environ.setdefault("SENDGRID_FROM_EMAIL", "test@example.com")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test.db")
os.environ.setdefault("CHROMA_PERSIST_DIR", "./test_chroma_db")


@pytest.fixture(scope="session")
def meta_app_secret() -> str:
    return os.environ["META_APP_SECRET"]
