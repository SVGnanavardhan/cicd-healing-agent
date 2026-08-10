import shutil
from pathlib import Path
from urllib.parse import urlparse, urlunparse

from git import Repo
from git.exc import GitCommandError


WORKSPACE_DIR = Path("workspace")


class RepositoryAgentError(Exception):
    pass


def validate_github_url(
    repository_url: str,
) -> None:
    parsed_url = urlparse(
        repository_url
    )

    if parsed_url.scheme not in {
        "http",
        "https",
    }:
        raise RepositoryAgentError(
            "Repository URL must use HTTP or HTTPS."
        )

    if (
        parsed_url.netloc.lower()
        != "github.com"
    ):
        raise RepositoryAgentError(
            "Only GitHub repository URLs are supported."
        )

    path_parts = [
        part
        for part in (
            parsed_url.path
            .strip("/")
            .split("/")
        )
        if part
    ]

    if len(path_parts) < 2:
        raise RepositoryAgentError(
            "Invalid GitHub repository URL."
        )


def build_authenticated_clone_url(
    repository_url: str,
    github_token: str | None = None,
) -> str:
    if not github_token:
        return repository_url

    parsed_url = urlparse(
        repository_url
    )

    authenticated_netloc = (
        f"x-access-token:"
        f"{github_token}@"
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
    safe_message = (
        error_message
        or "Unknown Git error"
    )

    if github_token:
        safe_message = (
            safe_message.replace(
                github_token,
                "***REDACTED***",
            )
        )

    return safe_message


def cleanup_repository_workspace(
    run_id: str,
) -> bool:
    run_directory = (
        WORKSPACE_DIR
        / run_id
    )

    if not run_directory.exists():
        return False

    try:
        shutil.rmtree(
            run_directory
        )
        return True

    except OSError:
        return False


def clone_repository(
    repository_url: str,
    run_id: str,
    github_token: str | None = None,
) -> Path:
    validate_github_url(
        repository_url
    )

    WORKSPACE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    run_directory = (
        WORKSPACE_DIR
        / run_id
    )

    repository_directory = (
        run_directory
        / "repository"
    )

    if run_directory.exists():
        shutil.rmtree(
            run_directory,
            ignore_errors=True,
        )

    run_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    clone_url = (
        build_authenticated_clone_url(
            repository_url=(
                repository_url
            ),
            github_token=(
                github_token
            ),
        )
    )

    try:
        repository = (
            Repo.clone_from(
                clone_url,
                repository_directory,
                depth=1,
                single_branch=True,
            )
        )

        try:
            origin = (
                repository.remote(
                    "origin"
                )
            )

            origin.set_url(
                repository_url
            )

        except Exception:
            pass

        return (
            repository_directory
        )

    except GitCommandError as error:
        shutil.rmtree(
            run_directory,
            ignore_errors=True,
        )

        raw_error = (
            error.stderr
            or str(error)
        )

        safe_error = (
            sanitize_git_error(
                error_message=(
                    raw_error
                ),
                github_token=(
                    github_token
                ),
            )
        )

        raise RepositoryAgentError(
            f"Repository clone failed: "
            f"{safe_error}"
        ) from error

    except Exception as error:
        shutil.rmtree(
            run_directory,
            ignore_errors=True,
        )

        safe_error = (
            sanitize_git_error(
                error_message=str(
                    error
                ),
                github_token=(
                    github_token
                ),
            )
        )

        raise RepositoryAgentError(
            f"Repository clone failed: "
            f"{safe_error}"
        ) from error