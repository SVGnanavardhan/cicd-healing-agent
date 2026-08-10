from pathlib import Path


class PathSecurityError(Exception):
    pass


def resolve_repository_file(
    repository_path: Path,
    relative_file: str,
) -> Path:
    if not relative_file:
        raise PathSecurityError(
            "Target file path is missing"
        )

    repository_root = (
        repository_path.resolve()
    )

    candidate = (
        repository_root
        / relative_file
    ).resolve()

    try:
        candidate.relative_to(
            repository_root
        )
    except ValueError as error:
        raise PathSecurityError(
            "Target path escapes repository workspace"
        ) from error

    return candidate


def ensure_editable_file(
    repository_path: Path,
    relative_file: str,
) -> Path:
    target = resolve_repository_file(
        repository_path,
        relative_file,
    )

    if not target.exists():
        raise PathSecurityError(
            f"Target file does not exist: {relative_file}"
        )

    if not target.is_file():
        raise PathSecurityError(
            f"Target path is not a file: {relative_file}"
        )

    return target