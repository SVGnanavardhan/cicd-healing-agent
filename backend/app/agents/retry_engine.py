from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.agents.failure_analysis_agent import (
    analyze_test_failures,
)
from app.agents.fix_apply_agent import (
    apply_generated_fixes,
)
from app.agents.fix_generator_agent import (
    generate_fix_suggestions,
)
from app.agents.test_execution_agent import (
    execute_detected_tests,
)


def utc_now_iso() -> str:
    return datetime.now(
        timezone.utc
    ).isoformat()


def get_verification_mode(
    detected_commands: list[
        dict[str, Any]
    ],
) -> str:
    if not detected_commands:
        return "NONE"

    frameworks = {
        str(
            command.get(
                "framework",
                "",
            )
        ).lower()
        for command
        in detected_commands
    }

    if frameworks and frameworks.issubset(
        {
            "python_compile",
            "notebook_verify",
        }
    ):
        return "STATIC_VERIFICATION"

    return "TEST_SUITE"


def all_commands_passed(
    results: list[
        dict[str, Any]
    ],
) -> bool:
    if not results:
        return False

    return all(
        result.get(
            "status"
        )
        == "PASSED"
        for result
        in results
    )


def count_applied_fixes(
    fixes: list[
        dict[str, Any]
    ],
) -> int:
    return sum(
        1
        for fix in fixes
        if fix.get(
            "apply_status"
        )
        == "APPLIED"
    )


def run_healing_iterations(
    repository_path: Path,
    detected_commands: list[
        dict[str, Any]
    ],
    retry_limit: int = 5,
) -> dict[str, Any]:
    safe_retry_limit = max(
        1,
        min(
            int(retry_limit),
            10,
        ),
    )

    verification_mode = (
        get_verification_mode(
            detected_commands
        )
    )

    if not detected_commands:
        return {
            "passed": False,
            "verification_mode":
                "NONE",
            "iterations_used": 0,
            "timeline": [],
            "test_results": [],
            "failures": [],
            "applied_fixes": [],
            "stop_reason":
                "NO_TESTS_FOUND",
        }

    timeline: list[
        dict[str, Any]
    ] = []

    all_applied_fixes: list[
        dict[str, Any]
    ] = []

    latest_test_results: list[
        dict[str, Any]
    ] = []

    latest_failures: list[
        dict[str, Any]
    ] = []

    for iteration in range(
        1,
        safe_retry_limit + 1,
    ):
        test_results = (
            execute_detected_tests(
                repository_path=(
                    repository_path
                ),
                detected_commands=(
                    detected_commands
                ),
            )
        )

        latest_test_results = (
            test_results
        )

        if all_commands_passed(
            test_results
        ):
            timeline_status = (
                "STATIC_VERIFICATION_PASSED"
                if verification_mode
                == "STATIC_VERIFICATION"
                else "PASSED"
            )

            timeline.append(
                {
                    "iteration":
                        iteration,

                    "status":
                        timeline_status,

                    "verification_mode":
                        verification_mode,

                    "timestamp":
                        utc_now_iso(),

                    "test_results":
                        test_results,

                    "failures":
                        [],
                }
            )

            return {
                "passed":
                    True,

                "verification_mode":
                    verification_mode,

                "iterations_used":
                    iteration,

                "timeline":
                    timeline,

                "test_results":
                    test_results,

                "failures":
                    [],

                "applied_fixes":
                    all_applied_fixes,

                "stop_reason":
                    (
                        "STATIC_VERIFICATION_PASSED"
                        if verification_mode
                        == "STATIC_VERIFICATION"
                        else "TESTS_PASSED"
                    ),
            }

        failures = (
            analyze_test_failures(
                test_results
            )
        )

        latest_failures = (
            failures
        )

        timeline_entry: dict[
            str,
            Any,
        ] = {
            "iteration":
                iteration,

            "status":
                "FAILED",

            "verification_mode":
                verification_mode,

            "timestamp":
                utc_now_iso(),

            "test_results":
                test_results,

            "failures":
                failures,
        }

        if not failures:
            timeline_entry[
                "stop_reason"
            ] = (
                "NO_ACTIONABLE_FIXES"
            )

            timeline.append(
                timeline_entry
            )

            return {
                "passed":
                    False,

                "verification_mode":
                    verification_mode,

                "iterations_used":
                    iteration,

                "timeline":
                    timeline,

                "test_results":
                    latest_test_results,

                "failures":
                    latest_failures,

                "applied_fixes":
                    all_applied_fixes,

                "stop_reason":
                    "NO_ACTIONABLE_FIXES",
            }

        suggestions = (
            generate_fix_suggestions(
                repository_path=(
                    repository_path
                ),
                failures=failures,
            )
        )

        timeline_entry[
            "generated_fixes"
        ] = suggestions

        if not suggestions:
            timeline_entry[
                "stop_reason"
            ] = (
                "NO_ACTIONABLE_FIXES"
            )

            timeline.append(
                timeline_entry
            )

            return {
                "passed":
                    False,

                "verification_mode":
                    verification_mode,

                "iterations_used":
                    iteration,

                "timeline":
                    timeline,

                "test_results":
                    latest_test_results,

                "failures":
                    latest_failures,

                "applied_fixes":
                    all_applied_fixes,

                "stop_reason":
                    "NO_ACTIONABLE_FIXES",
            }

        applied_fixes = (
            apply_generated_fixes(
                repository_path=(
                    repository_path
                ),
                suggestions=(
                    suggestions
                ),
            )
        )

        all_applied_fixes.extend(
            applied_fixes
        )

        applied_count = (
            count_applied_fixes(
                applied_fixes
            )
        )

        timeline_entry[
            "applied_fixes"
        ] = applied_fixes

        timeline_entry[
            "fixes_applied"
        ] = applied_count

        if applied_count == 0:
            timeline_entry[
                "stop_reason"
            ] = (
                "NO_ACTIONABLE_FIXES"
            )

            timeline.append(
                timeline_entry
            )

            return {
                "passed":
                    False,

                "verification_mode":
                    verification_mode,

                "iterations_used":
                    iteration,

                "timeline":
                    timeline,

                "test_results":
                    latest_test_results,

                "failures":
                    latest_failures,

                "applied_fixes":
                    all_applied_fixes,

                "stop_reason":
                    "NO_ACTIONABLE_FIXES",
            }

        timeline_entry[
            "status"
        ] = "FIX_APPLIED"

        timeline.append(
            timeline_entry
        )

    return {
        "passed":
            False,

        "verification_mode":
            verification_mode,

        "iterations_used":
            safe_retry_limit,

        "timeline":
            timeline,

        "test_results":
            latest_test_results,

        "failures":
            latest_failures,

        "applied_fixes":
            all_applied_fixes,

        "stop_reason":
            "RETRY_LIMIT_REACHED",
    }