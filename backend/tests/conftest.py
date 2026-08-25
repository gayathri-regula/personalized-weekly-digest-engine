"""Pytest fixtures for isolated in-memory test database and FastAPI TestClient."""

import asyncio
from datetime import datetime, timezone
from typing import AsyncGenerator
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.activity_item import ActivityItem
from app.models.user import User

# In-memory SQLite engine for test isolation
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
test_async_session = async_sessionmaker(
    bind=test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
def clear_llm_api_keys(monkeypatch):
    """Ensure LLM API keys are unset for every test to enforce deterministic fallback isolation."""
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)


@pytest.fixture(autouse=True)
async def setup_test_db():
    """Create all database tables in memory and seed test fixtures before each test."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with test_async_session() as session:
        # Seed test users
        u1 = User(id="user_1", name="Test User 1", interest_tags=["AI", "Python"])
        u2 = User(id="user_2", name="Test User 2", interest_tags=["Security"])
        u3 = User(
            id="user_3",
            name="Test User 3",
            interest_tags=["ObscureInterestWithZeroMatchingTags"],
        )
        session.add_all([u1, u2, u3])

        # Seed test activity items
        now = datetime(2026, 7, 25, 12, 0, 0, tzinfo=timezone.utc)
        item1 = ActivityItem(
            id="item_01",
            title="Optimizing LLM Inference",
            content="PyTorch compiler optimizations and Triton kernels.",
            category_tags=["AI", "Python"],
            created_at=now,
            engagement_metadata={"views": 500, "likes": 50, "shares": 10},
        )
        item2 = ActivityItem(
            id="item_02",
            title="Securing Biometric Authentication",
            content="Hardware Security Modules on iOS and Android.",
            category_tags=["Security"],
            created_at=now,
            engagement_metadata={"views": 300, "likes": 20, "shares": 5},
        )
        session.add_all([item1, item2])
        await session.commit()

    yield

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency override for get_db yielding a session from test_async_session."""
    async with test_async_session() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client for testing FastAPI endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
