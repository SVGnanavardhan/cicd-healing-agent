import re
import shutil
from pathlib import Path
from urllib.parse import quote, urlparse, urlunparse

from git import Repo
from git.exc import GitCommandError


WORKSPACE_ROOT = Path("workspace")


class RepositoryServiceError(Exception):
    pass


def validate_github_url(repository_url: str) -> None:
    parsed_url = urlparse(repository_url)

    if parsed_url.scheme not in {"http", "https"}:
        raise RepositoryServiceError(
            "Repository URL must use HTTP or HTTPS."
        )

    if parsed_url.netloc.lower() != "github.com":
        raise RepositoryServiceError(
            "Only GitHub repository URLs are currently supported."
        )

    path_parts = [
        part
        for part in parsed_url.path.strip("/").split("/")
        if part
    ]

    if len(path_parts) < 2:
        raise RepositoryServiceError(
            "Invalid GitHub repository URL."
        )


def extract_repository_name(
    repository_url: str,
) -> str:
    parsed_url = urlparse(repository_url)

    repository_name = Path(
        parsed_url.path.rstrip("/")
    ).name

    if repository_name.endswith(".git"):
        repository_name = repository_name[:-4]

    repository_name = re.sub(
        r"[^A-Za-z0-9._-]",
        "_",
        repository_name,
    )

    if not repository_name:
        raise RepositoryServiceError(
            "Unable to determine repository name."
        )

    return repository_name


def build_clone_url(
    repository_url: str,
    github_token: str | None = None,
) -> str:
    if not github_token:
        return repository_url

    parsed_url = urlparse(repository_url)

    encoded_token = quote(
        github_token,
        safe="",
    )

    authenticated_netloc = (
        f"x-access-token:{encoded_token}@"
        f"{parsed_url.netloc}"
    )

    return urlunparse(
        (
            parsed_url.scheme,
            authenticated_netloc,
            parsed_url.path,
            parsed_url.params,
            parsed_url.query,
            parsed_url.fragment,
        )
    )


def sanitize_git_error(
    error_message: str,
    github_token: str | None,
) -> str:
    sanitized_message = error_message

    if github_token:
        sanitized_message = sanitized_message.replace(
            github_token,
            "***REDACTED***",
        )

        encoded_token = quote(
            github_token,
            safe="",
        )

        sanitized_message = sanitized_message.replace(
            encoded_token,
            "***REDACTED***",
        )

    return sanitized_message


def clone_repository(
    repository_url: str,
    run_id: str,
    github_token: str | None = None,
) -> Path:
    validate_github_url(repository_url)

    repository_name = extract_repository_name(
        repository_url
    )

    run_workspace = WORKSPACE_ROOT / run_id
    repository_path = (
        run_workspace / repository_name
    )

    if run_workspace.exists():
        shutil.rmtree(
            run_workspace,
            ignore_errors=True,
        )

    run_workspace.mkdir(
        parents=True,
        exist_ok=True,
    )

    clone_url = build_clone_url(
        repository_url=repository_url,
        github_token=github_token,
    )

    try:
        Repo.clone_from(
            clone_url,
            repository_path,
            depth=1,
        )

    except GitCommandError as error:
        shutil.rmtree(
            run_workspace,
            ignore_errors=True,
        )

        safe_error = sanitize_git_error(
            error_message=str(error),
            github_token=github_token,
        )

        raise RepositoryServiceError(
            f"Repository clone failed: {safe_error}"
        ) from error

    return repository_path