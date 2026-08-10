import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


class EnvironmentSetupError(
    Exception
):
    pass


DEFAULT_TIMEOUT_SECONDS = 600


def run_setup_command(
    command: list[str],
    repository_path: Path,
    display_command: str,
    timeout_seconds: int = (
        DEFAULT_TIMEOUT_SECONDS
    ),
) -> dict[str, Any]:
    started_at = (
        time.perf_counter()
    )

    try:
        completed_process = (
            subprocess.run(
                command,
                cwd=repository_path,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                check=False,
            )
        )

        duration = (
            time.perf_counter()
            - started_at
        )

        return {
            "command":
                display_command,

            "status":
                (
                    "SUCCESS"
                    if (
                        completed_process.returncode
                        == 0
                    )
                    else "FAILED"
                ),

            "exit_code":
                completed_process.returncode,

            "duration_seconds":
                round(
                    duration,
                    2,
                ),

            "stdout":
                completed_process.stdout,

            "stderr":
                completed_process.stderr,
        }

    except subprocess.TimeoutExpired as error:
        duration = (
            time.perf_counter()
            - started_at
        )

        return {
            "command":
                display_command,

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
                (
                    error.stdout
                    if isinstance(
                        error.stdout,
                        str,
                    )
                    else ""
                ),

            "stderr":
                (
                    "Environment setup command "
                    "timed out"
                ),
        }

    except OSError as error:
        duration = (
            time.perf_counter()
            - started_at
        )

        return {
            "command":
                display_command,

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
                "",

            "stderr":
                str(error),
        }


def setup_python_environment(
    repository_path: Path,
) -> list[dict[str, Any]]:
    results: list[
        dict[str, Any]
    ] = []

    requirements_file = (
        repository_path
        / "requirements.txt"
    )

    pyproject_file = (
        repository_path
        / "pyproject.toml"
    )

    setup_file = (
        repository_path
        / "setup.py"
    )

    if requirements_file.exists():
        result = run_setup_command(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "-r",
                "requirements.txt",
                "--disable-pip-version-check",
            ],
            repository_path,
            (
                "python -m pip install "
                "-r requirements.txt"
            ),
        )

        results.append(
            result
        )

        return results

    if (
        pyproject_file.exists()
        or setup_file.exists()
    ):
        result = run_setup_command(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                ".",
                "--disable-pip-version-check",
            ],
            repository_path,
            "python -m pip install .",
        )

        results.append(
            result
        )

    return results


def get_node_install_command(
    repository_path: Path,
) -> tuple[
    list[str],
    str,
]:
    package_lock = (
        repository_path
        / "package-lock.json"
    )

    yarn_lock = (
        repository_path
        / "yarn.lock"
    )

    pnpm_lock = (
        repository_path
        / "pnpm-lock.yaml"
    )

    if pnpm_lock.exists():
        return (
            [
                "pnpm",
                "install",
                "--frozen-lockfile",
            ],
            (
                "pnpm install "
                "--frozen-lockfile"
            ),
        )

    if yarn_lock.exists():
        return (
            [
                "yarn",
                "install",
                "--frozen-lockfile",
            ],
            (
                "yarn install "
                "--frozen-lockfile"
            ),
        )

    if package_lock.exists():
        return (
            [
                "npm",
                "ci",
                "--no-audit",
                "--no-fund",
            ],
            (
                "npm ci "
                "--no-audit --no-fund"
            ),
        )

    return (
        [
            "npm",
            "install",
            "--no-audit",
            "--no-fund",
        ],
        (
            "npm install "
            "--no-audit --no-fund"
        ),
    )


def setup_node_environment(
    repository_path: Path,
) -> list[dict[str, Any]]:
    package_json = (
        repository_path
        / "package.json"
    )

    if not package_json.exists():
        return []

    try:
        json.loads(
            package_json.read_text(
                encoding="utf-8"
            )
        )

    except (
        OSError,
        json.JSONDecodeError,
    ):
        return [
            {
                "command":
                    "package.json validation",

                "status":
                    "FAILED",

                "exit_code":
                    None,

                "duration_seconds":
                    0,

                "stdout":
                    "",

                "stderr":
                    "Invalid package.json",
            }
        ]

    (
        install_command,
        display_command,
    ) = get_node_install_command(
        repository_path
    )

    first_result = run_setup_command(
        install_command,
        repository_path,
        display_command,
    )

    if (
        first_result["status"]
        == "SUCCESS"
    ):
        return [
            first_result
        ]

    if (
        install_command[0]
        == "npm"
        and install_command[1]
        == "ci"
    ):
        fallback_result = (
            run_setup_command(
                [
                    "npm",
                    "install",
                    "--no-audit",
                    "--no-fund",
                ],
                repository_path,
                (
                    "npm install "
                    "--no-audit --no-fund"
                ),
            )
        )

        fallback_result[
            "fallback_for"
        ] = display_command

        return [
            fallback_result
        ]

    return [
        first_result
    ]


def setup_repository_environment(
    repository_path: Path,
) -> list[dict[str, Any]]:
    if (
        not repository_path.exists()
        or not repository_path.is_dir()
    ):
        raise EnvironmentSetupError(
            "Repository path does not exist"
        )

    results: list[
        dict[str, Any]
    ] = []

    has_python_project = any(
        (
            repository_path
            / filename
        ).exists()
        for filename
        in (
            "requirements.txt",
            "pyproject.toml",
            "setup.py",
            "Pipfile",
        )
    )

    has_node_project = (
        repository_path
        / "package.json"
    ).exists()

    if has_python_project:
        python_results = (
            setup_python_environment(
                repository_path
            )
        )

        results.extend(
            python_results
        )

        if any(
            result.get(
                "status"
            )
            == "FAILED"
            for result
            in python_results
        ):
            return results

    if has_node_project:
        node_results = (
            setup_node_environment(
                repository_path
            )
        )

        results.extend(
            node_results
        )

        if any(
            result.get(
                "status"
            )
            == "FAILED"
            for result
            in node_results
        ):
            return results

    return results