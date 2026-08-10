import os
from typing import Any
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv


load_dotenv()


GITHUB_API_VERSION = "2022-11-28"


class PullRequestAgentError(Exception):
    pass


def extract_repository_details(
    repository_url: str,
) -> tuple[str, str]:
    parsed_url = urlparse(
        repository_url
    )

    if (
        parsed_url.scheme
        not in {
            "http",
            "https",
        }
    ):
        raise PullRequestAgentError(
            "Repository URL must use HTTP or HTTPS"
        )

    if (
        parsed_url.netloc.lower()
        != "github.com"
    ):
        raise PullRequestAgentError(
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
        raise PullRequestAgentError(
            "Invalid GitHub repository URL"
        )

    owner = path_parts[0]

    repository = (
        path_parts[1]
        .removesuffix(
            ".git"
        )
    )

    return (
        owner,
        repository,
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
        raise PullRequestAgentError(
            "GitHub token is required to create a pull request"
        )

    return token


def build_headers(
    github_token: str,
) -> dict[str, str]:
    return {
        "Accept":
            "application/vnd.github+json",

        "Authorization":
            f"Bearer {github_token}",

        "X-GitHub-Api-Version":
            GITHUB_API_VERSION,
    }


def safe_github_message(
    response: requests.Response,
    fallback: str,
) -> str:
    try:
        response_data = (
            response.json()
        )

        message = (
            response_data.get(
                "message"
            )
        )

        if message:
            return str(
                message
            )

    except ValueError:
        pass

    return fallback


def get_default_branch(
    owner: str,
    repository: str,
    github_token: str,
) -> str:
    api_url = (
        "https://api.github.com/"
        f"repos/{owner}/{repository}"
    )

    try:
        response = requests.get(
            api_url,
            headers=build_headers(
                github_token
            ),
            timeout=20,
        )

    except requests.Timeout as error:
        raise PullRequestAgentError(
            "Default branch detection timed out"
        ) from error

    except requests.RequestException as error:
        raise PullRequestAgentError(
            "Unable to connect to GitHub while detecting default branch"
        ) from error

    if response.status_code == 401:
        raise PullRequestAgentError(
            "Invalid or expired GitHub token"
        )

    if response.status_code == 403:
        raise PullRequestAgentError(
            safe_github_message(
                response,
                "GitHub denied repository access",
            )
        )

    if response.status_code == 404:
        raise PullRequestAgentError(
            "Repository not found or token has no access"
        )

    if response.status_code != 200:
        raise PullRequestAgentError(
            safe_github_message(
                response,
                (
                    "Unable to detect "
                    "repository default branch"
                ),
            )
        )

    try:
        repository_data = (
            response.json()
        )

    except ValueError as error:
        raise PullRequestAgentError(
            "Invalid repository response from GitHub"
        ) from error

    default_branch = (
        repository_data.get(
            "default_branch"
        )
    )

    if (
        not isinstance(
            default_branch,
            str,
        )
        or not default_branch.strip()
    ):
        raise PullRequestAgentError(
            "Repository default branch is missing"
        )

    return default_branch.strip()


def find_existing_pull_request(
    owner: str,
    repository: str,
    branch_name: str,
    base_branch: str,
    github_token: str,
) -> dict[str, Any] | None:
    api_url = (
        "https://api.github.com/"
        f"repos/{owner}/"
        f"{repository}/pulls"
    )

    params = {
        "state": "open",
        "head":
            f"{owner}:{branch_name}",
        "base":
            base_branch,
        "per_page":
            1,
    }

    try:
        response = requests.get(
            api_url,
            headers=build_headers(
                github_token
            ),
            params=params,
            timeout=20,
        )

    except requests.Timeout as error:
        raise PullRequestAgentError(
            "Pull request lookup timed out"
        ) from error

    except requests.RequestException as error:
        raise PullRequestAgentError(
            "Unable to check existing pull requests"
        ) from error

    if response.status_code == 401:
        raise PullRequestAgentError(
            "Invalid or expired GitHub token"
        )

    if response.status_code == 403:
        raise PullRequestAgentError(
            safe_github_message(
                response,
                "GitHub denied pull request access",
            )
        )

    if response.status_code != 200:
        raise PullRequestAgentError(
            safe_github_message(
                response,
                "Unable to check existing pull requests",
            )
        )

    try:
        pull_requests = (
            response.json()
        )

    except ValueError as error:
        raise PullRequestAgentError(
            "Invalid pull request response from GitHub"
        ) from error

    if (
        not isinstance(
            pull_requests,
            list,
        )
        or not pull_requests
    ):
        return None

    pull_request = (
        pull_requests[0]
    )

    return {
        "number":
            pull_request.get(
                "number"
            ),

        "url":
            pull_request.get(
                "html_url"
            ),

        "title":
            pull_request.get(
                "title"
            ),

        "state":
            pull_request.get(
                "state"
            ),

        "head_branch":
            branch_name,

        "base_branch":
            base_branch,

        "status":
            "ALREADY_EXISTS",
    }


def create_pull_request(
    repository_url: str,
    branch_name: str,
    github_token: str | None = None,
) -> dict[str, Any]:
    token = get_github_token(
        github_token
    )

    owner, repository = (
        extract_repository_details(
            repository_url
        )
    )

    base_branch = (
        get_default_branch(
            owner=owner,
            repository=repository,
            github_token=token,
        )
    )

    existing_pull_request = (
        find_existing_pull_request(
            owner=owner,
            repository=repository,
            branch_name=branch_name,
            base_branch=base_branch,
            github_token=token,
        )
    )

    if existing_pull_request:
        return existing_pull_request

    api_url = (
        "https://api.github.com/"
        f"repos/{owner}/"
        f"{repository}/pulls"
    )

    title = (
        "[AI-AGENT] "
        "Automated fixes for "
        f"{branch_name}"
    )

    payload = {
        "title":
            title,

        "head":
            branch_name,

        "base":
            base_branch,

        "body":
            (
                "This pull request was generated "
                "automatically by the Autonomous "
                "CI/CD Healing Agent.\n\n"
                "### Automated workflow\n"
                "- Repository tests executed\n"
                "- Failures analyzed\n"
                "- Verified fixes applied\n"
                "- Tests re-executed\n"
                "- Changes committed and pushed\n"
                "- CI/CD monitoring started"
            ),

        "maintainer_can_modify":
            True,

        "draft":
            False,
    }

    try:
        response = requests.post(
            api_url,
            headers=build_headers(
                token
            ),
            json=payload,
            timeout=30,
        )

    except requests.Timeout as error:
        raise PullRequestAgentError(
            "Pull request creation timed out"
        ) from error

    except requests.RequestException as error:
        raise PullRequestAgentError(
            "Unable to connect to GitHub while creating pull request"
        ) from error

    if response.status_code == 401:
        raise PullRequestAgentError(
            "Invalid or expired GitHub token"
        )

    if response.status_code == 403:
        raise PullRequestAgentError(
            safe_github_message(
                response,
                (
                    "GitHub token does not have "
                    "permission to create pull requests"
                ),
            )
        )

    if response.status_code == 404:
        raise PullRequestAgentError(
            "Repository not found or token has no access"
        )

    if response.status_code == 422:
        existing_pull_request = (
            find_existing_pull_request(
                owner=owner,
                repository=repository,
                branch_name=branch_name,
                base_branch=base_branch,
                github_token=token,
            )
        )

        if existing_pull_request:
            return existing_pull_request

        raise PullRequestAgentError(
            safe_github_message(
                response,
                (
                    "Pull request could not be created. "
                    "The branch may have no changes."
                ),
            )
        )

    if response.status_code != 201:
        raise PullRequestAgentError(
            safe_github_message(
                response,
                (
                    "Pull request creation failed "
                    f"with status {response.status_code}"
                ),
            )
        )

    try:
        response_data = (
            response.json()
        )

    except ValueError as error:
        raise PullRequestAgentError(
            "Invalid pull request response from GitHub"
        ) from error

    return {
        "number":
            response_data.get(
                "number"
            ),

        "url":
            response_data.get(
                "html_url"
            ),

        "title":
            response_data.get(
                "title",
                title,
            ),

        "state":
            response_data.get(
                "state"
            ),

        "head_branch":
            branch_name,

        "base_branch":
            base_branch,

        "status":
            "CREATED",
    }