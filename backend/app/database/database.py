import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import (
    DeclarativeBase,
    sessionmaker,
)


BACKEND_DIR = (
    Path(__file__)
    .resolve()
    .parents[2]
)

ENV_FILE = (
    BACKEND_DIR
    / ".env"
)

load_dotenv(
    dotenv_path=ENV_FILE
)


DATABASE_URL = (
    os.getenv(
        "DATABASE_URL",
        ""
    )
    .strip()
)


if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is missing in "
        f"{ENV_FILE}"
    )


class Base(
    DeclarativeBase
):
    pass


engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    future=True,
)


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)