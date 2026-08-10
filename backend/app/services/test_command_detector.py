import json
from pathlib import Path
from typing import Any


IGNORED_DIRECTORIES = {
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


def is_ignored_path(
    path: Path,
    repository_path: Path,
) -> bool:
    try:
        relative = path.relative_to(
            repository_path
        )
    except ValueError:
        return True

    return any(
        part in IGNORED_DIRECTORIES
        for part in relative.parts
    )


def read_package_json(
    repository_path: Path,
) -> dict[str, Any]:
    package_file = (
        repository_path
        / "package.json"
    )

    if not package_file.exists():
        return {}

    try:
        return json.loads(
            package_file.read_text(
                encoding="utf-8"
            )
        )
    except (
        OSError,
        json.JSONDecodeError,
    ):
        return {}


def python_source_exists(
    repository_path: Path,
) -> bool:
    try:
        for path in repository_path.rglob(
            "*.py"
        ):
            if (
                path.is_file()
                and not is_ignored_path(
                    path,
                    repository_path,
                )
            ):
                return True
    except OSError:
        return False

    return False


def notebook_source_exists(
    repository_path: Path,
) -> bool:
    try:
        for path in repository_path.rglob(
            "*.ipynb"
        ):
            if (
                path.is_file()
                and not is_ignored_path(
                    path,
                    repository_path,
                )
            ):
                return True
    except OSError:
        return False

    return False


def python_tests_exist(
    repository_path: Path,
) -> bool:
    patterns = [
        "test_*.py",
        "*_test.py",
    ]

    try:
        for pattern in patterns:
            for path in repository_path.rglob(
                pattern
            ):
                if (
                    path.is_file()
                    and not is_ignored_path(
                        path,
                        repository_path,
                    )
                ):
                    return True
    except OSError:
        return False

    return False


def detect_python_commands(
    repository_path: Path,
) -> list[dict[str, str]]:
    has_python = (
        python_source_exists(
            repository_path
        )
    )

    has_notebook = (
        notebook_source_exists(
            repository_path
        )
    )

    if not has_python and not has_notebook:
        return []

    if (
        has_python
        and python_tests_exist(
            repository_path
        )
    ):
        return [
            {
                "tool": "pytest",
                "language": "python",
                "framework": "pytest",
                "command": (
                    "python -m pytest"
                ),
            }
        ]

    commands: list[
        dict[str, str]
    ] = []

    if has_python:
        commands.append(
            {
                "tool": "python_compile",
                "language": "python",
                "framework": "python_compile",
                "command": (
                    "python -m compileall -q ."
                ),
            }
        )

    if has_notebook:
        commands.append(
            {
                "tool": "notebook_verify",
                "language": "python",
                "framework": "notebook_verify",
                "command": (
                    "__NOTEBOOK_VERIFY__"
                ),
            }
        )

    return commands


def detect_node_commands(
    repository_path: Path,
) -> list[dict[str, str]]:
    package_data = read_package_json(
        repository_path
    )

    if not package_data:
        return []

    scripts = (
        package_data.get(
            "scripts"
        )
        or {}
    )

    dependencies = {
        **(
            package_data.get(
                "dependencies"
            )
            or {}
        ),
        **(
            package_data.get(
                "devDependencies"
            )
            or {}
        ),
    }

    test_script = scripts.get(
        "test"
    )

    if "vitest" in dependencies:
        return [
            {
                "tool": "vitest",
                "language": "javascript",
                "framework": "vitest",
                "command": (
                    "npx vitest run"
                ),
            }
        ]

    if "jest" in dependencies:
        return [
            {
                "tool": "jest",
                "language": "javascript",
                "framework": "jest",
                "command": (
                    "npx jest --runInBand"
                ),
            }
        ]

    if (
        isinstance(
            test_script,
            str,
        )
        and test_script.strip()
        and "no test specified"
        not in test_script.lower()
    ):
        return [
            {
                "tool": "npm",
                "language": "javascript",
                "framework": "npm",
                "command": "npm test",
            }
        ]

    return []


def detect_test_commands(
    repository_path: Path,
) -> list[dict[str, str]]:
    commands: list[
        dict[str, str]
    ] = []

    commands.extend(
        detect_python_commands(
            repository_path
        )
    )

    commands.extend(
        detect_node_commands(
            repository_path
        )
    )

    unique_commands: list[
        dict[str, str]
    ] = []

    seen: set[str] = set()

    for item in commands:
        command = item.get(
            "command",
            ""
        )

        if (
            command
            and command not in seen
        ):
            seen.add(command)

            unique_commands.append(
                item
            )

    return unique_commands