import json
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select

from app.database.database import SessionLocal
from app.database.models import AuditLog


def parse_user_id(
    user_id: str | UUID,
) -> UUID:
    if isinstance(user_id, UUID):
        return user_id

    return UUID(user_id)


def create_audit_log(
    user_id: str | UUID,
    action: str,
    entity_type: str,
    entity_id: str | None = None,
    details: dict[str, Any] | None = None,
) -> None:
    parsed_user_id = parse_user_id(
        user_id
    )

    with SessionLocal() as session:
        record = AuditLog(
            id=str(uuid4()),
            user_id=parsed_user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details_json=json.dumps(
                details or {},
                ensure_ascii=False,
            ),
        )

        session.add(record)
        session.commit()


def list_audit_logs(
    user_id: str | UUID,
    limit: int = 50,
) -> list[dict[str, Any]]:
    parsed_user_id = parse_user_id(
        user_id
    )

    safe_limit = max(
        1,
        min(limit, 100),
    )

    with SessionLocal() as session:
        statement = (
            select(AuditLog)
            .where(
                AuditLog.user_id
                == parsed_user_id
            )
            .order_by(
                AuditLog.created_at.desc()
            )
            .limit(safe_limit)
        )

        records = session.scalars(
            statement
        ).all()

        activity: list[
            dict[str, Any]
        ] = []

        for record in records:
            try:
                details = json.loads(
                    record.details_json
                )
            except (
                json.JSONDecodeError,
                TypeError,
            ):
                details = {}

            activity.append(
                {
                    "id": record.id,
                    "action": record.action,
                    "entity_type": (
                        record.entity_type
                    ),
                    "entity_id": (
                        record.entity_id
                    ),
                    "details": details,
                    "created_at": (
                        record.created_at.isoformat()
                    ),
                }
            )

        return activity