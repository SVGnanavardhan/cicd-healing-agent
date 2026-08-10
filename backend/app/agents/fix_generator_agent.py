import re
from pathlib import Path
from typing import Any

from app.core.path_security import (
    PathSecurityError,
    ensure_editable_file,
)


JS_EXPECTED_RECEIVED_PATTERN = re.compile(
    r"""
    expected\s+
    (?P<received>-?\d+(?:\.\d+)?)
    \s+
    to\s+be\s+
    (?P<expected>-?\d+(?:\.\d+)?)
    """,
    re.IGNORECASE
    | re.VERBOSE,
)


TO_BE_PATTERN = re.compile(
    r"""
    (?P<prefix>
        \.toBe\(
    )
    (?P<value>
        -?\d+(?:\.\d+)?
    )
    (?P<suffix>
        \)
    )
    """,
    re.VERBOSE,
)


PYTHON_ASSERT_EQUAL_PATTERN = re.compile(
    r"""
    assert\s+
    (?P<left>.+?)
    \s*==\s*
    (?P<right>
        -?\d+(?:\.\d+)?
    )
    \s*$
    """,
    re.VERBOSE,
)


def read_target_line(
    repository_path: Path,
    relative_file: str,
    line_number: int,
) -> str | None:
    try:
        file_path = (
            ensure_editable_file(
                repository_path,
                relative_file,
            )
        )

        lines = (
            file_path.read_text(
                encoding="utf-8",
                errors="replace",
            )
            .splitlines()
        )

    except (
        OSError,
        PathSecurityError,
    ):
        return None

    index = (
        line_number - 1
    )

    if (
        index < 0
        or index >= len(lines)
    ):
        return None

    return lines[index]


def generate_javascript_assertion_fix(
    original_line: str,
    message: str,
) -> str | None:
    mismatch = (
        JS_EXPECTED_RECEIVED_PATTERN.search(
            message
        )
    )

    if not mismatch:
        return None

    received_value = (
        mismatch.group(
            "received"
        )
    )

    expected_value = (
        mismatch.group(
            "expected"
        )
    )

    assertion = (
        TO_BE_PATTERN.search(
            original_line
        )
    )

    if not assertion:
        return None

    current_value = (
        assertion.group(
            "value"
        )
    )

    if (
        current_value
        != expected_value
    ):
        return None

    return (
        original_line[
            :assertion.start(
                "value"
            )
        ]
        + received_value
        + original_line[
            assertion.end(
                "value"
            ):
        ]
    )


def generate_python_assertion_fix(
    original_line: str,
    message: str,
) -> str | None:
    mismatch = re.search(
        r"""
        assert\s+
        (?P<received>-?\d+(?:\.\d+)?)
        \s*==\s*
        (?P<expected>-?\d+(?:\.\d+)?)
        """,
        message,
        re.VERBOSE,
    )

    if not mismatch:
        return None

    assertion = (
        PYTHON_ASSERT_EQUAL_PATTERN.search(
            original_line.strip()
        )
    )

    if not assertion:
        return None

    expected_value = (
        mismatch.group(
            "expected"
        )
    )

    received_value = (
        mismatch.group(
            "received"
        )
    )

    if (
        assertion.group(
            "right"
        )
        != expected_value
    ):
        return None

    position = (
        original_line.rfind(
            expected_value
        )
    )

    if position < 0:
        return None

    return (
        original_line[
            :position
        ]
        + received_value
        + original_line[
            position
            + len(
                expected_value
            ):
        ]
    )


def generate_fix_suggestions(
    repository_path: Path,
    failures: list[
        dict[str, Any]
    ],
) -> list[dict[str, Any]]:
    suggestions: list[
        dict[str, Any]
    ] = []

    seen_targets: set[
        tuple[str, int]
    ] = set()

    for failure in failures:
        relative_file = (
            failure.get(
                "file"
            )
        )

        line_number = (
            failure.get(
                "line"
            )
        )

        if (
            not relative_file
            or not isinstance(
                line_number,
                int,
            )
            or line_number < 1
        ):
            continue

        target_key = (
            relative_file,
            line_number,
        )

        if target_key in seen_targets:
            continue

        original_line = (
            read_target_line(
                repository_path=(
                    repository_path
                ),
                relative_file=(
                    relative_file
                ),
                line_number=(
                    line_number
                ),
            )
        )

        if original_line is None:
            continue

        message = str(
            failure.get(
                "message",
                "",
            )
        )

        language = str(
            failure.get(
                "language",
                "",
            )
        ).lower()

        suggested_fix = None

        if (
            language
            in {
                "javascript",
                "typescript",
            }
            or relative_file.endswith(
                (
                    ".js",
                    ".jsx",
                    ".ts",
                    ".tsx",
                )
            )
        ):
            suggested_fix = (
                generate_javascript_assertion_fix(
                    original_line,
                    message,
                )
            )

        elif (
            language == "python"
            or relative_file.endswith(
                ".py"
            )
        ):
            suggested_fix = (
                generate_python_assertion_fix(
                    original_line,
                    message,
                )
            )

        if (
            not suggested_fix
            or suggested_fix
            == original_line
        ):
            continue

        suggestions.append(
            {
                "file":
                    relative_file,

                "line":
                    line_number,

                "bug_type":
                    failure.get(
                        "bug_type",
                        "LOGIC",
                    ),

                "original_line":
                    original_line,

                "suggested_fix":
                    suggested_fix,

                "reason":
                    (
                        "Deterministic assertion "
                        "mismatch repair"
                    ),

                "status":
                    "FIX_GENERATED",
            }
        )

        seen_targets.add(
            target_key
        )

    return suggestions