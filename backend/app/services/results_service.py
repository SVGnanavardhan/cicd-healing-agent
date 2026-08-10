import json
from pathlib import Path
from typing import Any


RESULTS_DIRECTORY = Path(
    "results"
)


class ResultsServiceError(
    Exception
):
    pass


def ensure_results_directory() -> None:
    RESULTS_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )


def get_results_file_path(
    run_id: str,
) -> Path:
    safe_run_id = (
        run_id
        .strip()
        .replace("/", "_")
        .replace("\\", "_")
    )

    if not safe_run_id:
        raise ResultsServiceError(
            "Run ID is required"
        )

    return (
        RESULTS_DIRECTORY
        / f"{safe_run_id}-results.json"
    )


def save_results(
    run_id: str,
    result_data: dict[str, Any],
) -> str:
    ensure_results_directory()

    file_path = (
        get_results_file_path(
            run_id
        )
    )

    temporary_path = (
        file_path.with_suffix(
            ".json.tmp"
        )
    )

    try:
        serialized_data = (
            json.dumps(
                result_data,
                ensure_ascii=False,
                indent=2,
                default=str,
            )
        )

        temporary_path.write_text(
            serialized_data,
            encoding="utf-8",
        )

        temporary_path.replace(
            file_path
        )

    except (
        OSError,
        TypeError,
        ValueError,
    ) as error:
        try:
            if (
                temporary_path.exists()
            ):
                temporary_path.unlink()

        except OSError:
            pass

        raise ResultsServiceError(
            "Unable to save results file"
        ) from error

    return str(
        file_path.resolve()
    )


def load_results(
    run_id: str,
) -> dict[str, Any] | None:
    file_path = (
        get_results_file_path(
            run_id
        )
    )

    if not file_path.exists():
        return None

    try:
        return json.loads(
            file_path.read_text(
                encoding="utf-8"
            )
        )

    except (
        OSError,
        json.JSONDecodeError,
    ) as error:
        raise ResultsServiceError(
            "Unable to read results file"
        ) from error


def delete_results(
    run_id: str,
) -> bool:
    file_path = (
        get_results_file_path(
            run_id
        )
    )

    if not file_path.exists():
        return False

    try:
        file_path.unlink()
        return True

    except OSError as error:
        raise ResultsServiceError(
            "Unable to delete results file"
        ) from error