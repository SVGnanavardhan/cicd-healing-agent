import json
from pathlib import Path
from typing import Any


def file_exists(
    repository_path: Path,
    filename: str,
) -> bool:
    return (
        repository_path
        / filename
    ).exists()


def detect_python_framework(
    repository_path: Path,
) -> str | None:
    requirements_files = [
        repository_path
        / "requirements.txt",

        repository_path
        / "pyproject.toml",

        repository_path
        / "Pipfile",
    ]

    dependency_text = ""

    for dependency_file in (
        requirements_files
    ):
        if (
            not dependency_file.exists()
            or not dependency_file.is_file()
        ):
            continue

        try:
            dependency_text += (
                dependency_file.read_text(
                    encoding="utf-8",
                    errors="ignore",
                ).lower()
            )

        except OSError:
            continue

    if "fastapi" in dependency_text:
        return "FastAPI"

    if "django" in dependency_text:
        return "Django"

    if "flask" in dependency_text:
        return "Flask"

    if "streamlit" in dependency_text:
        return "Streamlit"

    if "gradio" in dependency_text:
        return "Gradio"

    return None


def load_package_json(
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
                encoding="utf-8",
            )
        )

    except (
        OSError,
        json.JSONDecodeError,
    ):
        return {}


def detect_javascript_framework(
    repository_path: Path,
) -> str | None:
    package_data = (
        load_package_json(
            repository_path
        )
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

    if "next" in dependencies:
        return "Next.js"

    if "react" in dependencies:
        return "React"

    if "vue" in dependencies:
        return "Vue"

    if "@angular/core" in dependencies:
        return "Angular"

    if "svelte" in dependencies:
        return "Svelte"

    if "express" in dependencies:
        return "Express"

    return None


def detect_project_type(
    repository_path: Path,
) -> dict[str, Any]:
    if (
        not repository_path.exists()
        or not repository_path.is_dir()
    ):
        return {
            "project_type": "UNKNOWN",
            "languages": [],
            "frameworks": [],
            "package_managers": [],
            "detected_files": [],
        }

    detected_files: list[str] = []
    languages: list[str] = []
    frameworks: list[str] = []
    package_managers: list[str] = []

    python_markers = [
        "requirements.txt",
        "pyproject.toml",
        "setup.py",
        "Pipfile",
    ]

    node_markers = [
        "package.json",
        "package-lock.json",
        "yarn.lock",
        "pnpm-lock.yaml",
    ]

    for marker in (
        python_markers
        + node_markers
    ):
        if file_exists(
            repository_path,
            marker,
        ):
            detected_files.append(
                marker
            )

    python_files_exist = any(
        repository_path.rglob(
            "*.py"
        )
    )

    javascript_files_exist = any(
        repository_path.rglob(
            "*.js"
        )
    )

    typescript_files_exist = any(
        repository_path.rglob(
            "*.ts"
        )
    ) or any(
        repository_path.rglob(
            "*.tsx"
        )
    )

    if (
        python_files_exist
        or any(
            marker
            in detected_files
            for marker
            in python_markers
        )
    ):
        languages.append(
            "Python"
        )

        if (
            "requirements.txt"
            in detected_files
            or "setup.py"
            in detected_files
        ):
            package_managers.append(
                "pip"
            )

        if (
            "pyproject.toml"
            in detected_files
        ):
            package_managers.append(
                "pip/pyproject"
            )

        if (
            "Pipfile"
            in detected_files
        ):
            package_managers.append(
                "pipenv"
            )

        python_framework = (
            detect_python_framework(
                repository_path
            )
        )

        if python_framework:
            frameworks.append(
                python_framework
            )

    if (
        javascript_files_exist
        or typescript_files_exist
        or "package.json"
        in detected_files
    ):
        if typescript_files_exist:
            languages.append(
                "TypeScript"
            )

        if javascript_files_exist:
            languages.append(
                "JavaScript"
            )

        if (
            not javascript_files_exist
            and not typescript_files_exist
        ):
            languages.append(
                "JavaScript"
            )

        if (
            "pnpm-lock.yaml"
            in detected_files
        ):
            package_managers.append(
                "pnpm"
            )

        elif (
            "yarn.lock"
            in detected_files
        ):
            package_managers.append(
                "yarn"
            )

        else:
            package_managers.append(
                "npm"
            )

        javascript_framework = (
            detect_javascript_framework(
                repository_path
            )
        )

        if javascript_framework:
            frameworks.append(
                javascript_framework
            )

    languages = list(
        dict.fromkeys(
            languages
        )
    )

    frameworks = list(
        dict.fromkeys(
            frameworks
        )
    )

    package_managers = list(
        dict.fromkeys(
            package_managers
        )
    )

    has_python = (
        "Python"
        in languages
    )

    has_node = any(
        language
        in {
            "JavaScript",
            "TypeScript",
        }
        for language
        in languages
    )

    if (
        has_python
        and has_node
    ):
        project_type = (
            "FULL_STACK"
        )

    elif has_python:
        project_type = (
            "PYTHON"
        )

    elif has_node:
        project_type = (
            "NODE"
        )

    else:
        project_type = (
            "UNKNOWN"
        )

    return {
        "project_type":
            project_type,

        "languages":
            languages,

        "frameworks":
            frameworks,

        "package_managers":
            package_managers,

        "detected_files":
            detected_files,
    }