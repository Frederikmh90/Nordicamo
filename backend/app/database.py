"""Database connection and session management."""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from typing import Generator

from app.config import settings

# Defensive timeouts: prevent wedging API workers on slow connects/queries.
DB_CONNECT_TIMEOUT_SECONDS = int(os.getenv("DB_CONNECT_TIMEOUT_SECONDS", "5"))
DB_STATEMENT_TIMEOUT_MS = int(os.getenv("DB_STATEMENT_TIMEOUT_MS", "30000"))

# Create database engine
engine = create_engine(
    settings.database_url,
    poolclass=NullPool,  # Disable connection pooling for now
    pool_pre_ping=True,
    echo=False  # Set to True for SQL query logging
    ,
    connect_args={
        "connect_timeout": DB_CONNECT_TIMEOUT_SECONDS,
        # PostgreSQL server-side timeout for each statement, in ms.
        "options": f"-c statement_timeout={DB_STATEMENT_TIMEOUT_MS}",
    },
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Database session dependency for FastAPI.
    Yields a database session and closes it after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
