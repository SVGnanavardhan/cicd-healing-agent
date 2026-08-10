import json
import time
from pathlib import Path
from typing import Any

from app.core.command_runner import (
    execute_command,
)


class TestExecutionError(
    Exception
):
    pass


IGNORED_NOTEBOOK_DIRECTORIES = {
    ".git",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "__pycache__",
    "dist",
    "build",
    ".next",
}


def is_ignored_notebook(
    notebook_path: Path,
    repository_path: Path,
) -> bool:
    try:
        relative = (
            notebook_path.relative_to(
                repository_path
            )
        )
    except ValueError:
        return True

    return any(
        part in IGNORED_NOTEBOOK_DIRECTORIES
        for part in relative.parts
    )


def source_to_text(
    source: Any,
) -> str:
    if isinstance(
        source,
        str,
    ):
        return source

    if isinstance(
        source,
        list,
    ):
        return "".join(
            str(item)
            for item in source
        )

    return ""


def verify_notebooks(
    repository_path: Path,
) -> dict[str, Any]:
    started_at = (
        time.perf_counter()
    )

    notebook_files = [
        path
        for path
        in repository_path.rglob(
            "*.ipynb"
        )
        if (
            path.is_file()
            and not is_ignored_notebook(
                path,
                repository_path,
            )
        )
    ]

    if not notebook_files:
        return {
            "command":
                "__NOTEBOOK_VERIFY__",

            "tool":
                "notebook_verify",

            "language":
                "python",

            "framework":
                "notebook_verify",

            "status":
                "FAILED",

            "exit_code":
                1,

            "duration_seconds":
                round(
                    time.perf_counter()
                    - started_at,
                    2,
                ),

            "stdout":
                "",

            "stderr":
                "No Jupyter notebook files were found.",
        }

    checked_notebooks = 0
    checked_code_cells = 0

    failures: list[
        str
    ] = []

    for notebook_path in (
        notebook_files
    ):
        relative_path = (
            notebook_path
            .relative_to(
                repository_path
            )
            .as_posix()
        )

        try:
            notebook_data = (
                json.loads(
                    notebook_path.read_text(
                        encoding="utf-8",
                    )
                )
            )

        except (
            OSError,
            json.JSONDecodeError,
        ) as error:
            failures.append(
                (
                    f"{relative_path}: "
                    f"invalid notebook JSON: {error}"
                )
            )
            continue

        cells = notebook_data.get(
            "cells"
        )

        if not isinstance(
            cells,
            list,
        ):
            failures.append(
                (
                    f"{relative_path}: "
                    "missing or invalid cells array"
                )
            )
            continue

        checked_notebooks += 1

        for index, cell in enumerate(
            cells,
            start=1,
        ):
            if not isinstance(
                cell,
                dict,
            ):
                failures.append(
                    (
                        f"{relative_path}: "
                        f"cell {index} is invalid"
                    )
                )
                continue

            if (
                cell.get(
                    "cell_type"
                )
                != "code"
            ):
                continue

            source = source_to_text(
                cell.get(
                    "source",
                    ""
                )
            )

            if not source.strip():
                continue

            checked_code_cells += 1

            try:
                compile(
                    source,
                    (
                        f"{relative_path}"
                        f"#cell-{index}"
                    ),
                    "exec",
                )

            except SyntaxError as error:
                failures.append(
                    (
                        f"{relative_path}: "
                        f"code cell {index}: "
                        f"{error.msg}"
                        f" at line "
                        f"{error.lineno}"
                    )
                )

            except Exception as error:
                failures.append(
                    (
                        f"{relative_path}: "
                        f"code cell {index}: "
                        f"{error}"
                    )
                )

    duration = (
        time.perf_counter()
        - started_at
    )

    if failures:
        return {
            "command":
                "__NOTEBOOK_VERIFY__",

            "tool":
                "notebook_verify",

            "language":
                "python",

            "framework":
                "notebook_verify",

            "status":
                "FAILED",

            "exit_code":
                1,

            "duration_seconds":
                round(
                    duration,
                    2,
                ),

            "stdout":
                (
                    "Notebook verification completed.\n"
                    f"Notebooks checked: "
                    f"{checked_notebooks}\n"
                    f"Code cells checked: "
                    f"{checked_code_cells}"
                ),

            "stderr":
                "\n".join(
                    failures
                ),
        }

    return {
        "command":
            "__NOTEBOOK_VERIFY__",

        "tool":
            "notebook_verify",

        "language":
            "python",

        "framework":
            "notebook_verify",

        "status":
            "PASSED",

        "exit_code":
            0,

        "duration_seconds":
            round(
                duration,
                2,
            ),

        "stdout":
            (
                "Notebook static verification passed.\n"
                f"Notebooks checked: "
                f"{checked_notebooks}\n"
                f"Code cells checked: "
                f"{checked_code_cells}"
            ),

        "stderr":
            "",
    }


def execute_detected_tests(
    repository_path: Path,
    detected_commands: list[
        dict[str, Any]
    ],
) -> list[dict[str, Any]]:
    if (
        not repository_path.exists()
        or not repository_path.is_dir()
    ):
        raise TestExecutionError(
            "Repository path does not exist"
        )

    if not detected_commands:
        return []

    execution_results: list[
        dict[str, Any]
    ] = []

    for command_definition in (
        detected_commands
    ):
        command = str(
            command_definition.get(
                "command",
                "",
            )
        ).strip()

        framework = str(
            command_definition.get(
                "framework",
                "",
            )
        ).strip()

        if not command:
            continue

        if (
            framework
            == "notebook_verify"
            or command
            == "__NOTEBOOK_VERIFY__"
        ):
            result = (
                verify_notebooks(
                    repository_path
                )
            )

        else:
            result = (
                execute_command(
                    repository_path=(
                        repository_path
                    ),
                    command=command,
                    timeout_seconds=300,
                )
            )

            result["tool"] = (
                command_definition.get(
                    "tool",
                    "unknown",
                )
            )

            result["language"] = (
                command_definition.get(
                    "language",
                    "unknown",
                )
            )

            result["framework"] = (
                command_definition.get(
                    "framework",
                    "unknown",
                )
            )

        execution_results.append(
            result
        )

    return execution_results