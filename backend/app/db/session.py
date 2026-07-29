"""Async database engine and sessionmaker factory."""

import os
from typing import AsyncGenerator
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Load environment variables from .env
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL environment variable is missing in backend/.env. "
        "Please specify a valid async PostgreSQL connection string."
    )

connect_args = {}
if "asyncpg" in DATABASE_URL:
    connect_args["statement_cache_size"] = 0
    connect_args["prepared_statement_name_func"] = lambda *args, **kwargs: ""

engine = create_async_engine(
    DATABASE_URL, echo=False, future=True, connect_args=connect_args
)

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding an AsyncSession per request."""
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()
