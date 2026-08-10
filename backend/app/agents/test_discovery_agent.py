from pathlib import Path
from typing import Any


IGNORED_DIRECTORIES = {
    ".git",
    "node_modules",
    ".venv",
    "venv",
    "env",
    "dist",
    "build",
    "coverage",
    ".next",
    "__pycache__",
}


PYTHON_TEST_PATTERNS = (
    "test_*.py",
    "*_test.py",
)


JAVASCRIPT_TEST_SUFFIXES = (
    ".test.js",
    ".test.jsx",
    ".test.ts",
    ".test.tsx",
    ".spec.js",
    ".spec.jsx",
    ".spec.ts",
    ".spec.tsx",
)


def should_ignore(
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

    return any(
        part
        in IGNORED_DIRECTORIES
        for part
        in relative_path.parts
    )


def is_javascript_test(
    path: Path,
) -> bool:
    lowercase_name = (
        path.name.lower()
    )

    return any(
        lowercase_name.endswith(
            suffix
        )
        for suffix
        in JAVASCRIPT_TEST_SUFFIXES
    )


def discover_test_files(
    repository_path: Path,
) -> dict[str, Any]:
    if (
        not repository_path.exists()
        or not repository_path.is_dir()
    ):
        return {
            "total_test_files": 0,
            "test_files": [],
            "test_directories": [],
            "framework_hints": [],
        }

    discovered_files: set[
        str
    ] = set()

    test_directories: set[
        str
    ] = set()

    framework_hints: set[
        str
    ] = set()

    for pattern in (
        PYTHON_TEST_PATTERNS
    ):
        try:
            matches = (
                repository_path.rglob(
                    pattern
                )
            )

            for path in matches:
                if (
                    not path.is_file()
                    or should_ignore(
                        path,
                        repository_path,
                    )
                ):
                    continue

                relative = (
                    path.relative_to(
                        repository_path
                    )
                    .as_posix()
                )

                discovered_files.add(
                    relative
                )

                framework_hints.add(
                    "pytest"
                )

                if path.parent != repository_path:
                    test_directories.add(
                        path.parent
                        .relative_to(
                            repository_path
                        )
                        .as_posix()
                    )

        except OSError:
            continue

    try:
        for path in (
            repository_path.rglob(
                "*"
            )
        ):
            if (
                not path.is_file()
                or should_ignore(
                    path,
                    repository_path,
                )
            ):
                continue

            if not is_javascript_test(
                path
            ):
                continue

            relative = (
                path.relative_to(
                    repository_path
                )
                .as_posix()
            )

            discovered_files.add(
                relative
            )

            framework_hints.add(
                "javascript-test"
            )

            if path.parent != repository_path:
                test_directories.add(
                    path.parent
                    .relative_to(
                        repository_path
                    )
                    .as_posix()
                )

    except OSError:
        pass

    common_test_directories = [
        "tests",
        "test",
        "__tests__",
        "src/test",
        "src/tests",
    ]

    for directory_name in (
        common_test_directories
    ):
        directory = (
            repository_path
            / directory_name
        )

        if (
            directory.exists()
            and directory.is_dir()
        ):
            test_directories.add(
                directory_name
            )

    return {
        "total_test_files":
            len(
                discovered_files
            ),

        "test_files":
            sorted(
                discovered_files
            ),

        "test_directories":
            sorted(
                test_directories
            ),

        "framework_hints":
            sorted(
                framework_hints
            ),
    }