import re


ANSI_ESCAPE_PATTERN = re.compile(
    r"""
    \x1B
    (?:
        [@-_]
        |
        \[
        [0-?]*
        [ -/]*
        [@-~]
    )
    """,
    re.VERBOSE,
)


def remove_ansi_codes(
    text: str | None,
) -> str:
    return ANSI_ESCAPE_PATTERN.sub(
        "",
        text or "",
    )


def normalize_path(
    value: str,
) -> str:
    cleaned = (
        value.strip()
        .replace("\\", "/")
    )

    while cleaned.startswith(
        "./"
    ):
        cleaned = cleaned[2:]

    return cleaned


def clean_failure_message(
    value: str | None,
) -> str:
    text = remove_ansi_codes(
        value
    )

    return (
        text.strip()
    )