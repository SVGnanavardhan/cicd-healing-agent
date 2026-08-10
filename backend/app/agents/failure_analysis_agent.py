import re
from typing import Any

from app.core.text_utils import (
    clean_failure_message,
    normalize_path,
)


VITEST_LOCATION_PATTERN = re.compile(
    r"""
    (?P<file>
        [A-Za-z0-9_./\\@\-]+
        \.(?:js|jsx|ts|tsx)
    )
    :
    (?P<line>\d+)
    :
    (?P<column>\d+)
    """,
    re.VERBOSE,
)


PYTHON_TRACEBACK_PATTERN = re.compile(
    r"""
    File\s+"
    (?P<file>[^"]+)
    ",
    \s*line\s+
    (?P<line>\d+)
    """,
    re.VERBOSE,
)


PYTHON_SHORT_LOCATION_PATTERN = re.compile(
    r"""
    (?P<file>
        [A-Za-z0-9_./\\\-]+
        \.py
    )
    :
    (?P<line>\d+)
    """,
    re.VERBOSE,
)


def detect_bug_type(
    message: str,
) -> str:
    lowered = (
        message.lower()
    )

    if (
        "syntaxerror"
        in lowered
        or "syntax error"
        in lowered
    ):
        return "SYNTAX"

    if (
        "indentationerror"
        in lowered
        or "unexpected indent"
        in lowered
    ):
        return "INDENTATION"

    if (
        "modulenotfounderror"
        in lowered
        or "cannot find module"
        in lowered
        or "failed to resolve import"
        in lowered
    ):
        return "IMPORT"

    if (
        "typeerror"
        in lowered
        or "type error"
        in lowered
    ):
        return "TYPE_ERROR"

    if (
        "eslint"
        in lowered
        or "lint"
        in lowered
    ):
        return "LINTING"

    if (
        "assertionerror"
        in lowered
        or "expected"
        in lowered
        or "tobe("
        in lowered
        or "assert "
        in lowered
    ):
        return "LOGIC"

    return "UNKNOWN"


def find_location(
    message: str,
) -> tuple[
    str | None,
    int | None,
    int | None,
]:
    match = (
        VITEST_LOCATION_PATTERN.search(
            message
        )
    )

    if match:
        return (
            normalize_path(
                match.group(
                    "file"
                )
            ),
            int(
                match.group(
                    "line"
                )
            ),
            int(
                match.group(
                    "column"
                )
            ),
        )

    python_match = (
        PYTHON_TRACEBACK_PATTERN.search(
            message
        )
    )

    if python_match:
        return (
            normalize_path(
                python_match.group(
                    "file"
                )
            ),
            int(
                python_match.group(
                    "line"
                )
            ),
            None,
        )

    short_match = (
        PYTHON_SHORT_LOCATION_PATTERN.search(
            message
        )
    )

    if short_match:
        return (
            normalize_path(
                short_match.group(
                    "file"
                )
            ),
            int(
                short_match.group(
                    "line"
                )
            ),
            None,
        )

    return (
        None,
        None,
        None,
    )


def analyze_test_failures(
    execution_results: (
        list[dict[str, Any]]
        | None
    ),
) -> list[dict[str, Any]]:
    if not execution_results:
        return []

    failures: list[
        dict[str, Any]
    ] = []

    for result in (
        execution_results
    ):
        if (
            result.get(
                "status"
            )
            == "PASSED"
        ):
            continue

        stdout = (
            result.get(
                "stdout",
                ""
            )
            or ""
        )

        stderr = (
            result.get(
                "stderr",
                ""
            )
            or ""
        )

        message = (
            clean_failure_message(
                (
                    f"{stdout}\n"
                    f"{stderr}"
                )
            )
        )

        (
            file_path,
            line_number,
            column_number,
        ) = find_location(
            message
        )

        failures.append(
            {
                "tool":
                    result.get(
                        "tool",
                        "unknown",
                    ),

                "language":
                    result.get(
                        "language",
                        "unknown",
                    ),

                "framework":
                    result.get(
                        "framework",
                        "unknown",
                    ),

                "bug_type":
                    detect_bug_type(
                        message
                    ),

                "file":
                    file_path,

                "line":
                    line_number,

                "column":
                    column_number,

                "message":
                    message,

                "status":
                    "DETECTED",
            }
        )

    return failures