import os
import time
from datetime import (
    datetime,
    timezone,
)
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv


load_dotenv()


GITHUB_API_VERSION = "2022-11-28"


class CICDMonitorError(Exception):
    pass


def extract_owner_and_repo(
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
        raise CICDMonitorError(
            "Repository URL must use HTTP or HTTPS"
        )

    if (
        parsed_url.netloc.lower()
        != "github.com"
    ):
        raise CICDMonitorError(
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
        raise CICDMonitorError(
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
        raise CICDMonitorError(
            "GitHub token is required to monitor GitHub Actions"
        )

    return token


def build_headers(
    github_token: str,
) -> dict[str, str]:
    return {
        "Authorization":
            f"Bearer {github_token}",

        "Accept":
            "application/vnd.github+json",

        "X-GitHub-Api-Version":
            GITHUB_API_VERSION,
    }


def safe_api_message(
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


def monitor_github_actions(
    repository_url: str,
    branch_name: str,
    github_token: str | None = None,
    timeout_seconds: int = 90,
    poll_interval_seconds: int = 5,
) -> dict:
    token = get_github_token(
        github_token
    )

    owner, repository = (
        extract_owner_and_repo(
            repository_url
        )
    )

    safe_timeout = max(
        10,
        min(
            timeout_seconds,
            600,
        ),
    )

    safe_poll_interval = max(
        2,
        min(
            poll_interval_seconds,
            30,
        ),
    )

    api_url = (
        "https://api.github.com/"
        f"repos/{owner}/{repository}/"
        "actions/runs"
    )

    headers = build_headers(
        token
    )

    params = {
        "branch":
            branch_name,

        "event":
            "push",

        "per_page":
            5,
    }

    started_at = (
        time.monotonic()
    )

    timeline: list[dict] = []

    seen_states: set[
        tuple
    ] = set()

    no_run_attempts = 0

    while (
        time.monotonic()
        - started_at
        < safe_timeout
    ):
        try:
            response = (
                requests.get(
                    api_url,
                    headers=headers,
                    params=params,
                    timeout=20,
                )
            )

        except requests.Timeout as error:
            raise CICDMonitorError(
                "GitHub Actions request timed out"
            ) from error

        except requests.RequestException as error:
            raise CICDMonitorError(
                "Unable to connect to GitHub Actions"
            ) from error

        if response.status_code == 401:
            raise CICDMonitorError(
                "Invalid or expired GitHub token"
            )

        if response.status_code == 403:
            raise CICDMonitorError(
                safe_api_message(
                    response,
                    (
                        "GitHub token does not have "
                        "permission to read Actions"
                    ),
                )
            )

        if response.status_code == 404:
            raise CICDMonitorError(
                (
                    "Repository not found, Actions are unavailable, "
                    "or token has no access"
                )
            )

        if response.status_code != 200:
            raise CICDMonitorError(
                safe_api_message(
                    response,
                    (
                        "GitHub Actions API returned "
                        f"{response.status_code}"
                    ),
                )
            )

        try:
            response_data = (
                response.json()
            )

        except ValueError as error:
            raise CICDMonitorError(
                "Invalid GitHub Actions response"
            ) from error

        workflow_runs = (
            response_data.get(
                "workflow_runs",
                [],
            )
        )

        checked_at = (
            datetime.now(
                timezone.utc
            ).isoformat()
        )

        if not workflow_runs:
            no_run_attempts += 1

            state_key = (
                "NOT_FOUND",
                no_run_attempts,
            )

            if (
                state_key
                not in seen_states
            ):
                timeline.append(
                    {
                        "name":
                            "GitHub Actions",

                        "status":
                            "WAITING_FOR_WORKFLOW",

                        "conclusion":
                            None,

                        "workflow_run_id":
                            None,

                        "workflow_url":
                            None,

                        "checked_at":
                            checked_at,
                    }
                )

                seen_states.add(
                    state_key
                )

            if no_run_attempts >= 5:
                return {
                    "status":
                        "NOT_TRIGGERED",

                    "conclusion":
                        None,

                    "workflow_run_id":
                        None,

                    "workflow_url":
                        None,

                    "timeline":
                        timeline,

                    "detail":
                        (
                            "No GitHub Actions workflow run "
                            "was detected for the pushed branch"
                        ),
                }

            time.sleep(
                safe_poll_interval
            )

            continue

        no_run_attempts = 0

        branch_runs = [
            workflow_run
            for workflow_run
            in workflow_runs
            if (
                workflow_run.get(
                    "head_branch"
                )
                == branch_name
            )
        ]

        if not branch_runs:
            time.sleep(
                safe_poll_interval
            )
            continue

        workflow_run = max(
            branch_runs,
            key=lambda item:
                item.get(
                    "run_number",
                    0,
                )
                or 0,
        )

        workflow_status = (
            workflow_run.get(
                "status"
            )
        )

        conclusion = (
            workflow_run.get(
                "conclusion"
            )
        )

        workflow_run_id = (
            workflow_run.get(
                "id"
            )
        )

        workflow_url = (
            workflow_run.get(
                "html_url"
            )
        )

        workflow_name = (
            workflow_run.get(
                "name"
            )
            or "GitHub Actions"
        )

        state_key = (
            workflow_run_id,
            workflow_status,
            conclusion,
        )

        if (
            state_key
            not in seen_states
        ):
            timeline.append(
                {
                    "workflow_run_id":
                        workflow_run_id,

                    "name":
                        workflow_name,

                    "status":
                        workflow_status,

                    "conclusion":
                        conclusion,

                    "workflow_url":
                        workflow_url,

                    "checked_at":
                        checked_at,
                }
            )

            seen_states.add(
                state_key
            )

        if (
            workflow_status
            == "completed"
        ):
            if conclusion == "success":
                final_status = (
                    "PASSED"
                )

            elif conclusion in {
                "failure",
                "timed_out",
                "cancelled",
                "action_required",
                "startup_failure",
            }:
                final_status = (
                    "FAILED"
                )

            elif conclusion == "skipped":
                final_status = (
                    "SKIPPED"
                )

            else:
                final_status = (
                    "COMPLETED"
                )

            return {
                "status":
                    final_status,

                "conclusion":
                    conclusion,

                "workflow_run_id":
                    workflow_run_id,

                "workflow_url":
                    workflow_url,

                "workflow_name":
                    workflow_name,

                "timeline":
                    timeline,
            }

        time.sleep(
            safe_poll_interval
        )

    return {
        "status":
            "TIMEOUT",

        "conclusion":
            None,

        "workflow_run_id":
            (
                timeline[-1].get(
                    "workflow_run_id"
                )
                if timeline
                else None
            ),

        "workflow_url":
            (
                timeline[-1].get(
                    "workflow_url"
                )
                if timeline
                else None
            ),

        "timeline":
            timeline,

        "detail":
            (
                "GitHub Actions monitoring "
                "reached the timeout limit"
            ),
    }