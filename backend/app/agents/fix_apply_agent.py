from pathlib import Path
from typing import Any

from app.core.path_security import (
    PathSecurityError,
    ensure_editable_file,
)


def apply_single_fix(
    repository_path: Path,
    suggestion: dict[str, Any],
) -> dict[str, Any]:
    result = {
        **suggestion
    }

    relative_file = str(
        suggestion.get(
            "file",
            "",
        )
    )

    line_number = (
        suggestion.get(
            "line"
        )
    )

    original_line = (
        suggestion.get(
            "original_line"
        )
    )

    suggested_fix = (
        suggestion.get(
            "suggested_fix"
        )
    )

    if (
        not relative_file
        or not isinstance(
            line_number,
            int,
        )
        or line_number < 1
        or not isinstance(
            original_line,
            str,
        )
        or not isinstance(
            suggested_fix,
            str,
        )
    ):
        result[
            "apply_status"
        ] = "FAILED"

        result[
            "apply_error"
        ] = (
            "Invalid fix suggestion"
        )

        return result

    try:
        file_path = (
            ensure_editable_file(
                repository_path,
                relative_file,
            )
        )

    except PathSecurityError as error:
        result[
            "apply_status"
        ] = "FAILED"

        result[
            "apply_error"
        ] = str(
            error
        )

        return result

    try:
        text = (
            file_path.read_text(
                encoding="utf-8",
                errors="replace",
            )
        )

        newline = (
            "\r\n"
            if "\r\n" in text
            else "\n"
        )

        had_trailing_newline = (
            text.endswith(
                (
                    "\n",
                    "\r\n",
                )
            )
        )

        lines = (
            text.splitlines()
        )

        index = (
            line_number - 1
        )

        if (
            index < 0
            or index >= len(lines)
        ):
            result[
                "apply_status"
            ] = "FAILED"

            result[
                "apply_error"
            ] = (
                "Target line is outside file range"
            )

            return result

        current_line = (
            lines[index]
        )

        if (
            current_line
            != original_line
        ):
            result[
                "apply_status"
            ] = "FAILED"

            result[
                "apply_error"
            ] = (
                "Target line changed before fix "
                "could be applied"
            )

            result[
                "current_line"
            ] = current_line

            return result

        lines[index] = (
            suggested_fix
        )

        updated_text = (
            newline.join(
                lines
            )
        )

        if had_trailing_newline:
            updated_text += newline

        file_path.write_text(
            updated_text,
            encoding="utf-8",
        )

        result[
            "apply_status"
        ] = "APPLIED"

        return result

    except OSError as error:
        result[
            "apply_status"
        ] = "FAILED"

        result[
            "apply_error"
        ] = str(
            error
        )

        return result


def apply_generated_fixes(
    repository_path: Path,
    suggestions: list[
        dict[str, Any]
    ],
) -> list[dict[str, Any]]:
    applied_results: list[
        dict[str, Any]
    ] = []

    for suggestion in (
        suggestions
    ):
        applied_results.append(
            apply_single_fix(
                repository_path=(
                    repository_path
                ),
                suggestion=(
                    suggestion
                ),
            )
        )

    return applied_results