import os
import shlex
import subprocess
import time
from pathlib import Path
from typing import Any


DEFAULT_TIMEOUT_SECONDS = 300

MAX_OUTPUT_LENGTH = 200_000


class CommandRunnerError(Exception):
    pass


def truncate_output(
    value: str | None,
) -> str:
    text = value or ""

    if len(text) <= MAX_OUTPUT_LENGTH:
        return text

    return (
        text[:MAX_OUTPUT_LENGTH]
        + "\n\n[OUTPUT TRUNCATED]"
    )


def build_command_arguments(
    command: str,
) -> list[str]:
    cleaned_command = (
        command or ""
    ).strip()

    if not cleaned_command:
        raise CommandRunnerError(
            "Command is empty"
        )

    try:
        return shlex.split(
            cleaned_command,
            posix=(
                os.name != "nt"
            ),
        )

    except ValueError as error:
        raise CommandRunnerError(
            "Invalid command syntax"
        ) from error


def execute_command(
    repository_path: Path,
    command: str,
    timeout_seconds: int = (
        DEFAULT_TIMEOUT_SECONDS
    ),
) -> dict[str, Any]:
    if (
        not repository_path.exists()
        or not repository_path.is_dir()
    ):
        raise CommandRunnerError(
            "Repository directory does not exist"
        )

    arguments = build_command_arguments(
        command
    )

    timeout = max(
        10,
        min(
            int(timeout_seconds),
            900,
        ),
    )

    started_at = (
        time.perf_counter()
    )

    try:
        completed = subprocess.run(
            arguments,
            cwd=repository_path,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
            shell=False,
        )

        duration = (
            time.perf_counter()
            - started_at
        )

        return {
            "command":
                command,

            "status":
                (
                    "PASSED"
                    if completed.returncode == 0
                    else "FAILED"
                ),

            "exit_code":
                completed.returncode,

            "duration_seconds":
                round(
                    duration,
                    2,
                ),

            "stdout":
                truncate_output(
                    completed.stdout
                ),

            "stderr":
                truncate_output(
                    completed.stderr
                ),
        }

    except subprocess.TimeoutExpired as error:
        duration = (
            time.perf_counter()
            - started_at
        )

        return {
            "command":
                command,

            "status":
                "FAILED",

            "exit_code":
                None,

            "duration_seconds":
                round(
                    duration,
                    2,
                ),

            "stdout":
                truncate_output(
                    error.stdout
                    if isinstance(
                        error.stdout,
                        str,
                    )
                    else ""
                ),

            "stderr":
                (
                    "Command execution timed out"
                ),
        }

    except FileNotFoundError as error:
        return {
            "command":
                command,

            "status":
                "FAILED",

            "exit_code":
                None,

            "duration_seconds":
                round(
                    time.perf_counter()
                    - started_at,
                    2,
                ),

            "stdout":
                "",

            "stderr":
                (
                    "Command executable was not found: "
                    f"{arguments[0]}"
                ),
        }

    except OSError as error:
        return {
            "command":
                command,

            "status":
                "FAILED",

            "exit_code":
                None,

            "duration_seconds":
                round(
                    time.perf_counter()
                    - started_at,
                    2,
                ),

            "stdout":
                "",

            "stderr":
                str(error),
        }