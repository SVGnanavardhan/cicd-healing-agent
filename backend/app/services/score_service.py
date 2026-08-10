from typing import Any


MAX_SCORE = 100


def clamp_score(
    value: float,
) -> int:
    return max(
        0,
        min(
            MAX_SCORE,
            round(value),
        ),
    )


def calculate_score(
    total_duration_seconds: float,
    commit_count: int = 0,
    fixes_applied: int = 0,
    tests_passed: bool = True,
    ci_passed: bool | None = None,
) -> dict[str, Any]:
    duration = max(
        0.0,
        float(
            total_duration_seconds
            or 0
        ),
    )

    commits = max(
        0,
        int(
            commit_count
            or 0
        ),
    )

    fixes = max(
        0,
        int(
            fixes_applied
            or 0
        ),
    )

    if not tests_passed:
        return {
            "final_score": 0,
            "breakdown": {
                "test_score": 0,
                "speed_score": 0,
                "fix_score": 0,
                "git_score": 0,
                "ci_score": 0,
            },
        }

    test_score = 45

    if duration <= 30:
        speed_score = 20

    elif duration <= 60:
        speed_score = 18

    elif duration <= 120:
        speed_score = 15

    elif duration <= 300:
        speed_score = 10

    else:
        speed_score = 5

    if fixes > 0:
        fix_score = min(
            15,
            5 + fixes * 2,
        )
    else:
        fix_score = 5

    git_score = (
        10
        if commits > 0
        else 5
    )

    if ci_passed is True:
        ci_score = 10

    elif ci_passed is False:
        ci_score = 0

    else:
        ci_score = 5

    final_score = clamp_score(
        test_score
        + speed_score
        + fix_score
        + git_score
        + ci_score
    )

    return {
        "final_score": final_score,
        "breakdown": {
            "test_score": test_score,
            "speed_score": speed_score,
            "fix_score": fix_score,
            "git_score": git_score,
            "ci_score": ci_score,
        },
    }