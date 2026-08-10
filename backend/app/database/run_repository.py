import json
from typing import Any
from uuid import UUID

from sqlalchemy import delete, func, select

from app.database.database import SessionLocal
from app.database.models import RunRecord


def parse_user_id(
    user_id: str | UUID | None,
) -> UUID | None:
    if user_id is None:
        return None

    if isinstance(user_id, UUID):
        return user_id

    return UUID(user_id)


def save_run_db(
    result: dict[str, Any],
) -> None:
    with SessionLocal() as session:
        existing_record = session.get(
            RunRecord,
            result["run_id"],
        )

        result_json = json.dumps(
            result,
            ensure_ascii=False,
        )

        user_id = parse_user_id(
            result.get("user_id")
        )

        if existing_record:
            if user_id is not None:
                existing_record.user_id = user_id

            existing_record.repository_url = (
                result.get(
                    "repository_url",
                    existing_record.repository_url,
                )
            )

            existing_record.team_name = result.get(
                "team_name",
                existing_record.team_name,
            )

            existing_record.leader_name = result.get(
                "leader_name",
                existing_record.leader_name,
            )

            existing_record.branch_name = result.get(
                "branch_name",
                existing_record.branch_name,
            )

            existing_record.status = result.get(
                "status",
                existing_record.status,
            )

            existing_record.result_json = result_json

            existing_record.results_file = result.get(
                "results_file",
                existing_record.results_file,
            )

        else:
            record = RunRecord(
                run_id=result["run_id"],
                user_id=user_id,
                repository_url=result.get(
                    "repository_url",
                    "",
                ),
                team_name=result.get(
                    "team_name",
                    "",
                ),
                leader_name=result.get(
                    "leader_name",
                    "",
                ),
                branch_name=result.get(
                    "branch_name",
                    "",
                ),
                status=result.get(
                    "status",
                    "UNKNOWN",
                ),
                result_json=result_json,
                results_file=result.get(
                    "results_file"
                ),
            )

            session.add(record)

        session.commit()


def get_run_by_user_db(
    run_id: str,
    user_id: str,
) -> dict[str, Any] | None:
    parsed_user_id = parse_user_id(
        user_id
    )

    with SessionLocal() as session:
        statement = select(
            RunRecord
        ).where(
            RunRecord.run_id == run_id,
            RunRecord.user_id == parsed_user_id,
        )

        record = session.scalar(
            statement
        )

        if not record:
            return None

        return json.loads(
            record.result_json
        )


def list_runs_by_user_db(
    user_id: str,
    page: int = 1,
    page_size: int = 10,
    status_filter: str | None = None,
    search_query: str | None = None,
) -> dict[str, Any]:
    parsed_user_id = parse_user_id(
        user_id
    )

    safe_page = max(
        1,
        page,
    )

    safe_page_size = max(
        1,
        min(
            page_size,
            100,
        ),
    )

    offset = (
        safe_page - 1
    ) * safe_page_size

    with SessionLocal() as session:
        filters = [
            RunRecord.user_id
            == parsed_user_id
        ]

        if (
            status_filter
            and status_filter != "ALL"
        ):
            filters.append(
                RunRecord.status
                == status_filter
            )

        if search_query:
            cleaned_query = (
                search_query
                .strip()
            )

            if cleaned_query:
                search_value = (
                    f"%{cleaned_query}%"
                )

                filters.append(
                    RunRecord.repository_url.ilike(
                        search_value
                    )
                )

        count_statement = (
            select(
                func.count()
            )
            .select_from(
                RunRecord
            )
            .where(
                *filters
            )
        )

        total = (
            session.scalar(
                count_statement
            )
            or 0
        )

        statement = (
            select(
                RunRecord
            )
            .where(
                *filters
            )
            .order_by(
                RunRecord.created_at.desc()
            )
            .offset(
                offset
            )
            .limit(
                safe_page_size
            )
        )

        records = session.scalars(
            statement
        ).all()

        runs = [
            json.loads(
                record.result_json
            )
            for record in records
        ]

        total_pages = max(
            1,
            (
                total
                + safe_page_size
                - 1
            )
            // safe_page_size,
        )

        return {
            "runs": runs,
            "total": total,
            "page": safe_page,
            "page_size": safe_page_size,
            "total_pages": total_pages,
        }


def delete_run_by_user_db(
    run_id: str,
    user_id: str,
) -> bool:
    parsed_user_id = parse_user_id(
        user_id
    )

    with SessionLocal() as session:
        statement = (
            delete(
                RunRecord
            )
            .where(
                RunRecord.run_id
                == run_id,
                RunRecord.user_id
                == parsed_user_id,
            )
        )

        result = session.execute(
            statement
        )

        session.commit()

        return bool(
            result.rowcount
        )


def get_run_analytics_by_user_db(
    user_id: str,
) -> dict[str, Any]:
    parsed_user_id = parse_user_id(
        user_id
    )

    with SessionLocal() as session:
        statement = (
            select(
                RunRecord
            )
            .where(
                RunRecord.user_id
                == parsed_user_id
            )
        )

        records = session.scalars(
            statement
        ).all()

        runs = [
            json.loads(
                record.result_json
            )
            for record in records
        ]

    total_runs = len(
        runs
    )

    successful_statuses = {
        "TESTS_PASSED",
        "FIX_VERIFIED",
    }

    failed_statuses = {
        "FAILED",
        "RETRY_LIMIT_REACHED",
        "ENVIRONMENT_SETUP_FAILED",
        "NO_ACTIONABLE_FIXES",
        "NO_TESTS_FOUND",
    }

    successful_runs = sum(
        1
        for run in runs
        if run.get(
            "status"
        )
        in successful_statuses
    )

    failed_runs = sum(
        1
        for run in runs
        if run.get(
            "status"
        )
        in failed_statuses
    )

    cancelled_runs = sum(
        1
        for run in runs
        if run.get(
            "status"
        )
        == "CANCELLED"
    )

    total_fixes = sum(
        (
            run.get(
                "fix_application",
                {},
            )
            or {}
        ).get(
            "total_applied",
            0,
        )
        or 0
        for run in runs
    )

    total_pull_requests = sum(
        1
        for run in runs
        if (
            run.get(
                "pull_request"
            )
            and (
                run.get(
                    "pull_request",
                    {},
                ).get(
                    "status"
                )
                in {
                    "CREATED",
                    "ALREADY_EXISTS",
                }
            )
        )
    )

    durations: list[float] = []

    for run in runs:
        duration = run.get(
            "duration_seconds"
        )

        if duration is None:
            continue

        try:
            durations.append(
                float(
                    duration
                )
            )
        except (
            TypeError,
            ValueError,
        ):
            continue

    average_duration_seconds = (
        sum(
            durations
        )
        / len(
            durations
        )
        if durations
        else 0
    )

    success_rate = (
        round(
            (
                successful_runs
                / total_runs
            )
            * 100,
            2,
        )
        if total_runs
        else 0
    )

    return {
        "total_runs": total_runs,
        "successful_runs": successful_runs,
        "failed_runs": failed_runs,
        "cancelled_runs": cancelled_runs,
        "success_rate": success_rate,
        "total_fixes": total_fixes,
        "total_pull_requests": (
            total_pull_requests
        ),
        "average_duration_seconds": round(
            average_duration_seconds,
            2,
        ),
    }