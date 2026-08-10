import os
from pathlib import Path
from urllib.parse import (
    urlparse,
    urlunparse,
)

from dotenv import load_dotenv
from git import Repo
from git.exc import GitCommandError


load_dotenv()


class GitAgentError(Exception):
    pass


def validate_github_repository_url(
    repository_url: str,
) -> None:
    parsed_url = urlparse(
        repository_url
    )

    if parsed_url.scheme not in {
        "http",
        "https",
    }:
        raise GitAgentError(
            "Only HTTP or HTTPS repository URLs are supported"
        )

    if (
        parsed_url.netloc.lower()
        != "github.com"
    ):
        raise GitAgentError(
            "Only GitHub repository URLs are supported"
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
        raise GitAgentError(
            "Invalid GitHub repository URL"
        )


def get_github_token(
    github_token: str | None = None,
) -> str:
    token = (
        github_token
        or os.getenv(
            "GITHUB_TOKEN"
        )
        or ""
    ).strip()

    if not token:
        raise GitAgentError(
            "GitHub token is required to push changes"
        )

    return token


def build_authenticated_url(
    repository_url: str,
    github_token: str | None = None,
) -> str:
    validate_github_repository_url(
        repository_url
    )

    token = get_github_token(
        github_token
    )

    parsed_url = urlparse(
        repository_url
    )

    authenticated_netloc = (
        f"x-access-token:"
        f"{token}@"
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


def create_branch_commit_and_push(
    repository_path: Path,
    repository_url: str,
    branch_name: str,
    commit_message: str,
    github_token: str | None = None,
) -> dict:
    if not repository_path.exists():
        raise GitAgentError(
            "Repository path does not exist"
        )

    validate_github_repository_url(
        repository_url
    )

    token = get_github_token(
        github_token
    )

    try:
        repo = Repo(
            repository_path
        )

    except Exception as error:
        raise GitAgentError(
            "Unable to open cloned repository"
        ) from error

    if repo.bare:
        raise GitAgentError(
            "Repository is bare and cannot be modified"
        )

    try:
        origin = repo.remote(
            name="origin"
        )

    except ValueError as error:
        raise GitAgentError(
            "Git origin remote was not found"
        ) from error

    authenticated_url = (
        build_authenticated_url(
            repository_url=(
                repository_url
            ),
            github_token=token,
        )
    )

    original_remote_url = (
        origin.url
    )

    branch_created = False

    try:
        origin.set_url(
            authenticated_url
        )

        origin.fetch(
            prune=True
        )

        remote_branch_names = {
            reference.remote_head
            for reference
            in origin.refs
            if (
                reference.remote_head
                != "HEAD"
            )
        }

        if (
            branch_name
            in remote_branch_names
        ):
            raise GitAgentError(
                "Remote branch already exists"
            )

        repo.git.checkout(
            "-b",
            branch_name,
        )

        branch_created = True

        repo.git.add(
            A=True
        )

        if not repo.is_dirty(
            untracked_files=True
        ):
            return {
                "branch_name":
                    branch_name,
                "commit_created":
                    False,
                "commit_sha":
                    None,
                "commit_message":
                    None,
                "push_status":
                    "SKIPPED",
                "reason":
                    "No changes detected",
            }

        final_commit_message = (
            commit_message
            if commit_message.startswith(
                "[AI-AGENT]"
            )
            else (
                "[AI-AGENT] "
                f"{commit_message}"
            )
        )

        commit = (
            repo.index.commit(
                final_commit_message
            )
        )

        push_results = (
            origin.push(
                refspec=(
                    f"{branch_name}:"
                    f"{branch_name}"
                ),
                set_upstream=True,
            )
        )

        for push_result in (
            push_results
        ):
            if (
                push_result.flags
                & push_result.ERROR
            ):
                raise GitAgentError(
                    push_result.summary
                    or "Git push failed"
                )

        return {
            "branch_name":
                branch_name,
            "commit_created":
                True,
            "commit_sha":
                commit.hexsha,
            "commit_message":
                commit.message.strip(),
            "push_status":
                "PUSHED",
        }

    except GitCommandError as error:
        raw_error = (
            error.stderr
            or str(error)
        )

        safe_error = (
            sanitize_git_error(
                error_message=(
                    raw_error
                ),
                github_token=token,
            )
        )

        raise GitAgentError(
            safe_error
        ) from error

    except GitAgentError:
        raise

    except Exception as error:
        safe_error = (
            sanitize_git_error(
                error_message=str(
                    error
                ),
                github_token=token,
            )
        )

        raise GitAgentError(
            safe_error
        ) from error

    finally:
        try:
            origin.set_url(
                original_remote_url
            )
        except Exception:
            pass

        if branch_created:
            try:
                current_branch = (
                    repo.active_branch.name
                )

                if (
                    current_branch
                    != branch_name
                ):
                    pass
            except Exception:
                pass