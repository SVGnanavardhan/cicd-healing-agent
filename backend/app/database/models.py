from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import DateTime, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database.database import Base


class RunRecord(Base):
    __tablename__ = "runs"

    run_id: Mapped[str] = mapped_column(
        String(100),
        primary_key=True,
    )

    user_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        nullable=True,
        index=True,
    )

    repository_url: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    team_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    leader_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    branch_name: Mapped[str] = mapped_column(
        String(300),
        nullable=False,
        default="",
    )

    status: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    result_json: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    results_file: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(
            timezone.utc
        ),
        nullable=False,
        index=True,
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(
        String(100),
        primary_key=True,
    )

    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        nullable=False,
        index=True,
    )

    action: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    entity_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    entity_id: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        index=True,
    )

    details_json: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="{}",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(
            timezone.utc
        ),
        nullable=False,
        index=True,
    )