from pathlib import Path


IGNORED_DIRECTORIES = {
    ".git",
    ".idea",
    ".vscode",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    "coverage",
    ".next",
    ".venv",
    "venv",
    "env",
}


IGNORED_FILES = {
    ".DS_Store",
    "Thumbs.db",
}


MAX_FILES = 5000


def should_ignore_path(
    path: Path,
    repository_path: Path,
) -> bool:
    try:
        relative_path = (
            path.relative_to(
                repository_path
            )
        )

    except ValueError:
        return True

    for part in (
        relative_path.parts
    ):
        if (
            part
            in IGNORED_DIRECTORIES
        ):
            return True

    if (
        path.name
        in IGNORED_FILES
    ):
        return True

    return False


def scan_repository_structure(
    repository_path: Path,
) -> list[str]:
    if (
        not repository_path.exists()
        or not repository_path.is_dir()
    ):
        return []

    files: list[str] = []

    try:
        paths = (
            repository_path.rglob(
                "*"
            )
        )

        for path in paths:
            if len(files) >= MAX_FILES:
                break

            if should_ignore_path(
                path,
                repository_path,
            ):
                continue

            if not path.is_file():
                continue

            try:
                relative_path = (
                    path.relative_to(
                        repository_path
                    )
                )

            except ValueError:
                continue

            files.append(
                relative_path
                .as_posix()
            )

    except OSError:
        return files

    files.sort()

    return files