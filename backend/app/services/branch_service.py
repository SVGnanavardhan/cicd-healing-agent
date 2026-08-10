import re
from datetime import (
    datetime,
    timezone,
)


MAX_BRANCH_COMPONENT_LENGTH = 40


def sanitize_branch_component(
    value: str,
) -> str:
    cleaned = (
        value.strip().lower()
    )

    cleaned = re.sub(
        r"[^a-z0-9._-]+",
        "-",
        cleaned,
    )

    cleaned = re.sub(
        r"-+",
        "-",
        cleaned,
    )

    cleaned = (
        cleaned
        .strip(
            "-._"
        )
    )

    if not cleaned:
        return "user"

    return cleaned[
        :MAX_BRANCH_COMPONENT_LENGTH
    ]


def generate_branch_name(
    team_name: str,
    leader_name: str,
) -> str:
    team = (
        sanitize_branch_component(
            team_name
        )
    )

    leader = (
        sanitize_branch_component(
            leader_name
        )
    )

    timestamp = (
        datetime.now(
            timezone.utc
        )
        .strftime(
            "%Y%m%d-%H%M%S"
        )
    )

    return (
        "ai-healing/"
        f"{team}-"
        f"{leader}-"
        f"{timestamp}"
    )