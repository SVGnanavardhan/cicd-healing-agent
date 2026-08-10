from typing import Any

import requests


GITHUB_API_VERSION = "2022-11-28"
GITHUB_USER_API = "https://api.github.com/user"


class GitHubAuthError(Exception):
    pass


def build_github_headers(
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
        data = response.json()

        message = data.get("message")

        if message:
            return str(message)

    except ValueError:
        pass

    return fallback


def verify_github_token(
    github_token: str,
) -> dict[str, Any]:
    token = github_token.strip()

    if not token:
        raise GitHubAuthError(
            "GitHub token is required"
        )

    try:
        response = requests.get(
            GITHUB_USER_API,
            headers=build_github_headers(
                token
            ),
            timeout=20,
        )

    except requests.Timeout as error:
        raise GitHubAuthError(
            "GitHub verification timed out"
        ) from error

    except requests.RequestException as error:
        raise GitHubAuthError(
            "Unable to connect to GitHub"
        ) from error

    if response.status_code == 401:
        raise GitHubAuthError(
            "Invalid or expired GitHub token"
        )

    if response.status_code == 403:
        raise GitHubAuthError(
            get_api_message(
                response,
                "GitHub denied access for this token",
            )
        )

    if response.status_code != 200:
        raise GitHubAuthError(
            get_api_message(
                response,
                (
                    "GitHub verification failed "
                    f"with status {response.status_code}"
                ),
            )
        )

    try:
        user_data = response.json()

    except ValueError as error:
        raise GitHubAuthError(
            "Invalid response received from GitHub"
        ) from error

    login = user_data.get("login")

    if (
        not isinstance(login, str)
        or not login.strip()
    ):
        raise GitHubAuthError(
            "GitHub account information is missing"
        )

    oauth_scopes = response.headers.get(
        "X-OAuth-Scopes",
        "",
    )

    rate_limit_remaining = (
        response.headers.get(
            "X-RateLimit-Remaining"
        )
    )

    rate_limit_limit = (
        response.headers.get(
            "X-RateLimit-Limit"
        )
    )

    return {
        "verified": True,
        "login": login,
        "name": user_data.get("name"),
        "avatar_url": user_data.get(
            "avatar_url"
        ),
        "profile_url": user_data.get(
            "html_url"
        ),
        "account_type": user_data.get(
            "type"
        ),
        "user_id": user_data.get("id"),
        "public_repos": user_data.get(
            "public_repos"
        ),
        "private_repos": user_data.get(
            "total_private_repos"
        ),
        "scopes": [
            scope.strip()
            for scope in oauth_scopes.split(",")
            if scope.strip()
        ],
        "rate_limit": {
            "remaining": (
                int(rate_limit_remaining)
                if (
                    rate_limit_remaining
                    and rate_limit_remaining.isdigit()
                )
                else None
            ),
            "limit": (
                int(rate_limit_limit)
                if (
                    rate_limit_limit
                    and rate_limit_limit.isdigit()
                )
                else None
            ),
        },
    }