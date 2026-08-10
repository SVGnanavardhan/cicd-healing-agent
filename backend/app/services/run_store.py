import json
from pathlib import Path
from threading import Lock
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[3]
RESULTS_DIRECTORY = PROJECT_ROOT / "results"

_RUNS: dict[str, dict[str, Any]] = {}
_LOCK = Lock()


def _is_owned_by_user(
    run_data: dict[str, Any],
    user_id: str | None,
) -> bool:
    if user_id is None:
        return True

    return run_data.get("user_id") == user_id


def _read_results_file(
    results_file: Path,
) -> dict[str, Any] | None:
    try:
        data = json.loads(
            results_file.read_text(
                encoding="utf-8",
            )
        )

        if not isinstance(data, dict):
            return None

        return data

    except (OSError, json.JSONDecodeError):
        return None


def save_run(
    run_id: str,
    data: dict[str, Any],
) -> None:
    safe_data = dict(data)

    safe_data["run_id"] = run_id

    # GitHub token should never be stored.
    safe_data.pop("github_token", None)

    with _LOCK:
        _RUNS[run_id] = safe_data


def get_run(
    run_id: str,
    user_id: str | None = None,
) -> dict[str, Any] | None:
    with _LOCK:
        run_data = _RUNS.get(run_id)

        if run_data:
            run_data = dict(run_data)

    if run_data:
        if not _is_owned_by_user(
            run_data,
            user_id,
        ):
            return None

        return run_data

    results_file = (
        RESULTS_DIRECTORY
        / run_id
        / "results.json"
    )

    if not results_file.exists():
        return None

    run_data = _read_results_file(results_file)

    if not run_data:
        return None

    if not _is_owned_by_user(
        run_data,
        user_id,
    ):
        return None

    with _LOCK:
        _RUNS[run_id] = run_data

    return dict(run_data)


def list_runs(
    user_id: str | None = None,
) -> list[dict[str, Any]]:
    collected_runs: dict[
        str,
        dict[str, Any],
    ] = {}

    with _LOCK:
        memory_runs = [
            dict(run_data)
            for run_data in _RUNS.values()
        ]

    for run_data in memory_runs:
        run_id = run_data.get("run_id")

        if not run_id:
            continue

        if not _is_owned_by_user(
            run_data,
            user_id,
        ):
            continue

        collected_runs[run_id] = run_data

    if RESULTS_DIRECTORY.exists():
        for run_directory in RESULTS_DIRECTORY.iterdir():
            if not run_directory.is_dir():
                continue

            results_file = (
                run_directory
                / "results.json"
            )

            if not results_file.exists():
                continue

            run_data = _read_results_file(
                results_file
            )

            if not run_data:
                continue

            run_id = run_data.get(
                "run_id",
                run_directory.name,
            )

            if not _is_owned_by_user(
                run_data,
                user_id,
            ):
                continue

            collected_runs.setdefault(
                run_id,
                run_data,
            )

    runs = list(collected_runs.values())

    runs.sort(
        key=lambda item: item.get(
            "created_at",
            "",
        ),
        reverse=True,
    )

    return runs


def delete_run(
    run_id: str,
    user_id: str | None = None,
) -> bool:
    existing_run = get_run(
        run_id=run_id,
        user_id=user_id,
    )

    if not existing_run:
        return False

    with _LOCK:
        _RUNS.pop(run_id, None)

    return True