from typing import Any
from urllib.parse import urlparse

import requests


GITHUB_API_VERSION = "2022-11-28"


class GitHubRepositoryAccessError(
    Exception
):
    pass


def extract_repository_details(
    repository_url: str,
) -> tuple[str, str]:
    parsed_url = urlparse(
        repository_url
    )

    if parsed_url.scheme not in {
        "http",
        "https",
    }:
        raise GitHubRepositoryAccessError(
            "Repository URL must use HTTP or HTTPS"
        )

    if (
        parsed_url.netloc.lower()
        != "github.com"
    ):
        raise GitHubRepositoryAccessError(
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
        raise GitHubRepositoryAccessError(
            "Invalid GitHub repository URL"
        )

    owner = path_parts[0]

    repository = (
        path_parts[1]
        .removesuffix(".git")
    )

    if not owner or not repository:
        raise GitHubRepositoryAccessError(
            "Invalid GitHub repository URL"
        )

    return owner, repository


def build_headers(
    github_token: str,
) -> dict[str, str]:
    return {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {github_token}",
        "X-GitHub-Api-Version": GITHUB_API_VERSION,
    }


def get_api_message(
    response: requests.Response,
    fallback: str,
) -> str:
    try:
        response_data = response.json()

        message = response_data.get(
            "message"
        )

        if message:
            return str(message)

    except ValueError:
        pass

    return fallback


def verify_repository_access(
    repository_url: str,
    github_token: str,
) -> dict[str, Any]:
    token = github_token.strip()

    if not token:
        raise GitHubRepositoryAccessError(
            "GitHub token is required"
        )

    owner, repository = (
        extract_repository_details(
            repository_url
        )
    )

    api_url = (
        "https://api.github.com/repos/"
        f"{owner}/{repository}"
    )

    try:
        response = requests.get(
            api_url,
            headers=build_headers(
                token
            ),
            timeout=20,
        )

    except requests.Timeout as error:
        raise GitHubRepositoryAccessError(
            "Repository access verification timed out"
        ) from error

    except requests.RequestException as error:
        raise GitHubRepositoryAccessError(
            "Unable to connect to GitHub"
        ) from error

    if response.status_code == 401:
        raise GitHubRepositoryAccessError(
            "Invalid or expired GitHub token"
        )

    if response.status_code == 403:
        raise GitHubRepositoryAccessError(
            get_api_message(
                response,
                "GitHub denied repository access",
            )
        )

    if response.status_code == 404:
        raise GitHubRepositoryAccessError(
            (
                "Repository not found or "
                "the GitHub token has no access"
            )
        )

    if response.status_code != 200:
        raise GitHubRepositoryAccessError(
            get_api_message(
                response,
                (
                    "Repository verification failed "
                    f"with status {response.status_code}"
                ),
            )
        )

    try:
        repository_data = (
            response.json()
        )

    except ValueError as error:
        raise GitHubRepositoryAccessError(
            "Invalid repository response from GitHub"
        ) from error

    permissions = (
        repository_data.get(
            "permissions"
        )
        or {}
    )

    can_admin = bool(
        permissions.get("admin")
    )

    can_maintain = bool(
        permissions.get("maintain")
    )

    can_push = bool(
        permissions.get("push")
        or can_maintain
        or can_admin
    )

    can_triage = bool(
        permissions.get("triage")
    )

    can_pull = bool(
        permissions.get("pull")
        or can_triage
        or can_push
        or can_maintain
        or can_admin
    )

    return {
        "verified": True,
        "owner": owner,
        "repository": repository,
        "full_name": repository_data.get(
            "full_name"
        ),
        "private": bool(
            repository_data.get(
                "private",
                False,
            )
        ),
        "fork": bool(
            repository_data.get(
                "fork",
                False,
            )
        ),
        "archived": bool(
            repository_data.get(
                "archived",
                False,
            )
        ),
        "disabled": bool(
            repository_data.get(
                "disabled",
                False,
            )
        ),
        "default_branch": (
            repository_data.get(
                "default_branch"
            )
            or "main"
        ),
        "html_url": repository_data.get(
            "html_url"
        ),
        "clone_url": repository_data.get(
            "clone_url"
        ),
        "permissions": {
            "can_read": can_pull,
            "can_triage": can_triage,
            "can_push": can_push,
            "can_maintain": can_maintain,
            "can_admin": can_admin,
            "can_create_pull_request": (
                can_push
            ),
        },
    }