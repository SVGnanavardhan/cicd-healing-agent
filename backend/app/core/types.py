from typing import Any, TypedDict


class CommandDefinition(TypedDict, total=False):
    tool: str
    language: str
    framework: str
    command: str


class ExecutionResult(TypedDict, total=False):
    command: str
    tool: str
    language: str
    framework: str
    status: str
    exit_code: int | None
    duration_seconds: float
    stdout: str
    stderr: str


class FailureRecord(TypedDict, total=False):
    tool: str
    language: str
    framework: str
    bug_type: str
    file: str | None
    line: int | None
    column: int | None
    message: str
    status: str


class FixSuggestion(TypedDict, total=False):
    file: str
    line: int | None
    bug_type: str
    original_line: str
    suggested_fix: str
    reason: str
    status: str
    apply_status: str


JsonDict = dict[str, Any]