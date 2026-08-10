from datetime import datetime, timezone
from pathlib import Path
from threading import Event, Lock, Thread
from typing import Any
from uuid import uuid4

import os
import time

from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Query,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse


# ============================================================
# AUTH
# ============================================================

from app.auth.supabase_auth import (
    AuthenticatedUser,
    get_current_user,
)


# ============================================================
# DATABASE
# ============================================================

from app.database import models
from app.database.database import (
    Base,
    engine,
)
from app.services.pdf_report_service import (
    PDFReportError,
    create_results_pdf,
)
from app.database.run_repository import (
    delete_run_by_user_db,
    get_run_analytics_by_user_db,
    get_run_by_user_db,
    list_runs_by_user_db,
    save_run_db,
)

from app.database.audit_repository import (
    create_audit_log,
    list_audit_logs,
)


# ============================================================
# REQUEST MODELS
# ============================================================

from app.models.github_repository_request import (
    GitHubRepositoryRequest,
)

from app.models.github_token_request import (
    GitHubTokenRequest,
)

from app.models.run_request import (
    RunRequest,
)

from app.models.run_retry_request import (
    RunRetryRequest,
)


# ============================================================
# AGENTS
# ============================================================

from app.agents.cicd_monitor_agent import (
    CICDMonitorError,
    monitor_github_actions,
)

from app.agents.environment_setup_agent import (
    setup_repository_environment,
)

from app.agents.git_agent import (
    GitAgentError,
    create_branch_commit_and_push,
)

from app.agents.pull_request_agent import (
    PullRequestAgentError,
    create_pull_request,
)

from app.agents.repository_agent import (
    RepositoryAgentError,
    cleanup_repository_workspace,
    clone_repository,
)

from app.agents.retry_engine import (
    run_healing_iterations,
)

from app.agents.test_discovery_agent import (
    discover_test_files,
)


# ============================================================
# SERVICES
# ============================================================

from app.services.branch_service import (
    generate_branch_name,
)

from app.services.github_auth_service import (
    GitHubAuthError,
    verify_github_token,
)

from app.services.github_repository_service import (
    GitHubRepositoryAccessError,
    verify_repository_access,
)

from app.services.project_detection_service import (
    detect_project_type,
)

from app.services.results_service import (
    ResultsServiceError,
    delete_results,
    save_results,
)

from app.services.score_service import (
    calculate_score,
)

from app.services.structure_scanner import (
    scan_repository_structure,
)

from app.services.test_command_detector import (
    detect_test_commands,
)


# ============================================================
# APPLICATION
# ============================================================

app = FastAPI(
    title="Autonomous CI/CD Healing Agent",
    description=(
        "Repository analysis and automated "
        "code-fixing API"
    ),
    version="1.0.0",
)


Base.metadata.create_all(
    bind=engine
)


frontend_origins = [
    origin.strip()
    for origin in os.getenv(
        "FRONTEND_ORIGINS",
        (
            "http://localhost:5173,"
            "http://127.0.0.1:5173,"
            "http://localhost:4173,"
            "http://127.0.0.1:4173"
        ),
    ).split(",")
    if origin.strip()
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=frontend_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# WORKER REGISTRY
# ============================================================

RUN_CANCELLATION_EVENTS: dict[
    str,
    Event,
] = {}

RUN_THREADS: dict[
    str,
    Thread,
] = {}

RUN_REGISTRY_LOCK = Lock()


class RunCancelledError(
    Exception
):
    pass


def register_run_worker(
    run_id: str,
    worker: Thread,
    cancellation_event: Event,
) -> None:
    with RUN_REGISTRY_LOCK:
        RUN_THREADS[
            run_id
        ] = worker

        RUN_CANCELLATION_EVENTS[
            run_id
        ] = cancellation_event


def unregister_run_worker(
    run_id: str,
) -> None:
    with RUN_REGISTRY_LOCK:
        RUN_THREADS.pop(
            run_id,
            None,
        )

        RUN_CANCELLATION_EVENTS.pop(
            run_id,
            None,
        )


def get_run_cancellation_event(
    run_id: str,
) -> Event | None:
    with RUN_REGISTRY_LOCK:
        return (
            RUN_CANCELLATION_EVENTS
            .get(
                run_id
            )
        )


def raise_if_cancelled(
    cancellation_event: Event,
) -> None:
    if (
        cancellation_event
        .is_set()
    ):
        raise RunCancelledError(
            "Run cancelled by user"
        )


def get_active_worker_count() -> int:
    with RUN_REGISTRY_LOCK:
        return sum(
            1
            for worker
            in RUN_THREADS.values()
            if worker.is_alive()
        )


# ============================================================
# HELPERS
# ============================================================

def utc_now() -> str:
    return (
        datetime.now(
            timezone.utc
        ).isoformat()
    )


def build_progress(
    stage: str,
    message: str,
) -> dict[str, str]:
    return {
        "stage": stage,
        "message": message,
        "updated_at": utc_now(),
    }


def save_progress(
    run_id: str,
    user_id: str,
    request: RunRequest,
    status: str,
    stage: str,
    message: str,
) -> None:
    current_data = (
        get_run_by_user_db(
            run_id=run_id,
            user_id=user_id,
        )
        or {}
    )

    updated_data = {
        **current_data,
        "run_id":
            run_id,
        "user_id":
            user_id,
        "repository_url":
            str(
                request.repository_url
            ),
        "team_name":
            request.team_name,
        "leader_name":
            request.leader_name,
        "retry_limit":
            request.retry_limit,
        "status":
            status,
        "progress":
            build_progress(
                stage,
                message,
            ),
    }

    save_run_db(
        updated_data
    )


def calculate_run_score(
    duration_seconds: float,
    applied_fixes: list[
        dict[str, Any]
    ],
    fix_verified: bool,
    git_result: dict | None,
    cicd_result: dict | None,
) -> dict[str, Any]:

    applied_count = sum(
        1
        for fix
        in applied_fixes
        if fix.get(
            "apply_status"
        )
        == "APPLIED"
    )

    commit_count = (
        1
        if (
            git_result
            and git_result.get(
                "commit_created"
            )
        )
        else 0
    )

    ci_passed: bool | None = None

    if cicd_result:
        cicd_status = (
            cicd_result.get(
                "status"
            )
        )

        if cicd_status == "PASSED":
            ci_passed = True

        elif cicd_status == "FAILED":
            ci_passed = False

    return calculate_score(
        total_duration_seconds=(
            duration_seconds
        ),
        commit_count=(
            commit_count
        ),
        fixes_applied=(
            applied_count
        ),
        tests_passed=(
            fix_verified
        ),
        ci_passed=(
            ci_passed
        ),
    )


# ============================================================
# PUBLIC ENDPOINTS
# ============================================================

@app.get("/")
def root():
    return {
        "message":
            (
                "Autonomous CI/CD "
                "Healing Agent API"
            ),
        "status":
            "running",
    }


@app.get("/api/health")
def health_check():
    return {
        "status":
            "healthy",
        "service":
            "cicd-agent-backend",
        "active_workers":
            get_active_worker_count(),
    }


# ============================================================
# GITHUB ENDPOINTS
# ============================================================

@app.post("/api/github/verify")
def verify_github_access(
    request: GitHubTokenRequest,
    current_user: (
        AuthenticatedUser
    ) = Depends(
        get_current_user
    ),
):
    try:
        github_user = (
            verify_github_token(
                request.github_token
            )
        )

    except GitHubAuthError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    try:
        create_audit_log(
            user_id=(
                current_user.user_id
            ),
            action=(
                "GITHUB_VERIFIED"
            ),
            entity_type=(
                "github_account"
            ),
            entity_id=(
                github_user.get(
                    "login"
                )
            ),
            details={
                "github_username":
                    github_user.get(
                        "login"
                    ),
            },
        )
    except Exception:
        pass

    return {
        "status":
            "CONNECTED",
        "user_id":
            current_user.user_id,
        "github":
            github_user,
    }


@app.post(
    "/api/github/repository-access"
)
def check_github_repository_access(
    request: GitHubRepositoryRequest,
    current_user: (
        AuthenticatedUser
    ) = Depends(
        get_current_user
    ),
):
    try:
        repository_access = (
            verify_repository_access(
                repository_url=str(
                    request.repository_url
                ),
                github_token=(
                    request.github_token
                ),
            )
        )

    except GitHubRepositoryAccessError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    try:
        create_audit_log(
            user_id=(
                current_user.user_id
            ),
            action=(
                "REPOSITORY_VERIFIED"
            ),
            entity_type=(
                "repository"
            ),
            entity_id=(
                repository_access.get(
                    "full_name"
                )
            ),
            details={
                "repository_url":
                    str(
                        request.repository_url
                    ),
                "private":
                    repository_access.get(
                        "private"
                    ),
                "permissions":
                    repository_access.get(
                        "permissions"
                    ),
            },
        )
    except Exception:
        pass

    return {
        "status":
            "ACCESS_VERIFIED",
        "user_id":
            current_user.user_id,
        "repository":
            repository_access,
    }


# ============================================================
# RUN START
# ============================================================

@app.post("/api/runs/start")
def start_run(
    request: RunRequest,
    current_user: (
        AuthenticatedUser
    ) = Depends(
        get_current_user
    ),
):
    run_id = str(
        uuid4()
    )

    initial_data = {
        "run_id":
            run_id,

        "user_id":
            current_user.user_id,

        "repository_url":
            str(
                request.repository_url
            ),

        "team_name":
            request.team_name,

        "leader_name":
            request.leader_name,

        "retry_limit":
            request.retry_limit,

        "status":
            "QUEUED",

        "progress":
            build_progress(
                "QUEUED",
                (
                    "Run is waiting "
                    "to start."
                ),
            ),

        "created_at":
            utc_now(),
    }

    save_run_db(
        initial_data
    )

    try:
        create_audit_log(
            user_id=(
                current_user.user_id
            ),
            action=(
                "RUN_STARTED"
            ),
            entity_type=(
                "run"
            ),
            entity_id=(
                run_id
            ),
            details={
                "repository_url":
                    str(
                        request.repository_url
                    ),
                "team_name":
                    request.team_name,
                "leader_name":
                    request.leader_name,
            },
        )
    except Exception:
        pass

    cancellation_event = (
        Event()
    )

    worker = Thread(
        target=process_run,
        args=(
            request,
            run_id,
            current_user.user_id,
            cancellation_event,
        ),
        daemon=True,
    )

    register_run_worker(
        run_id=run_id,
        worker=worker,
        cancellation_event=(
            cancellation_event
        ),
    )

    worker.start()

    return initial_data


# ============================================================
# MAIN AUTONOMOUS PIPELINE
# ============================================================

def process_run(
    request: RunRequest,
    run_id: str,
    user_id: str,
    cancellation_event: Event,
) -> None:

    run_started_at = (
        time.perf_counter()
    )

    repository_path: (
        Path | None
    ) = None

    project_info: dict[
        str,
        Any,
    ] = {}

    repository_files: list[
        str
    ] = []

    test_discovery: dict[
        str,
        Any,
    ] = {}

    detected_test_commands: list[
        dict[str, Any]
    ] = []

    environment_setup_results: list[
        dict[str, Any]
    ] = []

    detected_failures: list[
        dict[str, Any]
    ] = []

    applied_fixes: list[
        dict[str, Any]
    ] = []

    verification_results: list[
        dict[str, Any]
    ] = []

    environment_ready = False
    fix_verified = False

    git_result = None
    pull_request_result = None
    cicd_result = None

    healing_result: dict[
        str,
        Any,
    ] = {
        "passed":
            False,
        "verification_mode":
            "NONE",
        "iterations_used":
            0,
        "timeline":
            [],
        "test_results":
            [],
        "failures":
            [],
        "applied_fixes":
            [],
        "stop_reason":
            None,
    }

    branch_base = (
        generate_branch_name(
            team_name=(
                request.team_name
            ),
            leader_name=(
                request.leader_name
            ),
        )
    )

    short_run_id = (
        run_id
        .split("-")[0]
        .lower()
    )

    branch_name = (
        f"{branch_base}-"
        f"{short_run_id}"
    )

    try:
        save_progress(
            run_id,
            user_id,
            request,
            "RUNNING",
            "CLONING_REPOSITORY",
            (
                "Cloning GitHub "
                "repository."
            ),
        )

        raise_if_cancelled(
            cancellation_event
        )

        repository_path = (
            clone_repository(
                repository_url=str(
                    request.repository_url
                ),
                run_id=run_id,
                github_token=(
                    request.github_token
                ),
            )
        )

        raise_if_cancelled(
            cancellation_event
        )

        save_progress(
            run_id,
            user_id,
            request,
            "RUNNING",
            "DETECTING_PROJECT",
            (
                "Detecting project "
                "type and structure."
            ),
        )

        project_info = (
            detect_project_type(
                repository_path
            )
        )

        repository_files = (
            scan_repository_structure(
                repository_path
            )
        )

        test_discovery = (
            discover_test_files(
                repository_path
            )
        )

        detected_test_commands = (
            detect_test_commands(
                repository_path
            )
        )

        raise_if_cancelled(
            cancellation_event
        )

        save_progress(
            run_id,
            user_id,
            request,
            "RUNNING",
            "SETTING_UP_ENVIRONMENT",
            (
                "Installing repository "
                "dependencies."
            ),
        )

        environment_setup_results = (
            setup_repository_environment(
                repository_path
            )
        )

        environment_ready = (
            not environment_setup_results
            or all(
                result.get(
                    "status"
                )
                == "SUCCESS"
                for result
                in environment_setup_results
            )
        )

        raise_if_cancelled(
            cancellation_event
        )

        if environment_ready:

            save_progress(
                run_id,
                user_id,
                request,
                "RUNNING",
                "HEALING",
                (
                    "Executing verification "
                    "and healing iterations."
                ),
            )

            healing_result = (
                run_healing_iterations(
                    repository_path=(
                        repository_path
                    ),
                    detected_commands=(
                        detected_test_commands
                    ),
                    retry_limit=(
                        request.retry_limit
                    ),
                )
            )

        fix_verified = bool(
            healing_result.get(
                "passed",
                False,
            )
        )

        verification_results = (
            healing_result.get(
                "test_results",
                [],
            )
            or []
        )

        detected_failures = (
            healing_result.get(
                "failures",
                [],
            )
            or []
        )

        applied_fixes = (
            healing_result.get(
                "applied_fixes",
                [],
            )
            or []
        )

        raise_if_cancelled(
            cancellation_event
        )

        # ----------------------------------------------------
        # GIT PUSH
        # ----------------------------------------------------

        actual_applied_fixes = [
            fix
            for fix
            in applied_fixes
            if fix.get(
                "apply_status"
            )
            == "APPLIED"
        ]

        if (
            fix_verified
            and actual_applied_fixes
        ):
            save_progress(
                run_id,
                user_id,
                request,
                "RUNNING",
                "PUSHING_FIXES",
                (
                    "Creating Git branch, "
                    "commit and push."
                ),
            )

            try:
                git_result = (
                    create_branch_commit_and_push(
                        repository_path=(
                            repository_path
                        ),
                        repository_url=str(
                            request.repository_url
                        ),
                        branch_name=(
                            branch_name
                        ),
                        commit_message=(
                            "Apply verified "
                            "automated fixes"
                        ),
                        github_token=(
                            request.github_token
                        ),
                    )
                )

            except GitAgentError as error:
                git_result = {
                    "branch_name":
                        branch_name,
                    "commit_created":
                        False,
                    "commit_sha":
                        None,
                    "commit_message":
                        None,
                    "push_status":
                        "FAILED",
                    "detail":
                        str(error),
                }

        # ----------------------------------------------------
        # PR + CI
        # ----------------------------------------------------

        if (
            git_result
            and git_result.get(
                "push_status"
            )
            == "PUSHED"
        ):
            raise_if_cancelled(
                cancellation_event
            )

            save_progress(
                run_id,
                user_id,
                request,
                "RUNNING",
                "CREATING_PULL_REQUEST",
                (
                    "Creating GitHub "
                    "pull request."
                ),
            )

            try:
                pull_request_result = (
                    create_pull_request(
                        repository_url=str(
                            request.repository_url
                        ),
                        branch_name=(
                            branch_name
                        ),
                        github_token=(
                            request.github_token
                        ),
                    )
                )

            except PullRequestAgentError as error:
                pull_request_result = {
                    "status":
                        "CREATION_FAILED",
                    "number":
                        None,
                    "url":
                        None,
                    "title":
                        None,
                    "state":
                        None,
                    "detail":
                        str(error),
                }

            raise_if_cancelled(
                cancellation_event
            )

            save_progress(
                run_id,
                user_id,
                request,
                "RUNNING",
                "MONITORING_CI",
                (
                    "Monitoring GitHub "
                    "Actions."
                ),
            )

            try:
                cicd_result = (
                    monitor_github_actions(
                        repository_url=str(
                            request.repository_url
                        ),
                        branch_name=(
                            branch_name
                        ),
                        github_token=(
                            request.github_token
                        ),
                    )
                )

            except CICDMonitorError as error:
                cicd_result = {
                    "status":
                        "MONITOR_FAILED",
                    "detail":
                        str(error),
                    "timeline":
                        [],
                }

        elif fix_verified:
            cicd_result = {
                "status":
                    "NOT_TRIGGERED",
                "detail":
                    (
                        "No verified code changes "
                        "were pushed."
                    ),
                "timeline":
                    [],
            }

        # ----------------------------------------------------
        # STATUS
        # ----------------------------------------------------

        stop_reason = (
            healing_result.get(
                "stop_reason"
            )
        )

        verification_mode = (
            healing_result.get(
                "verification_mode",
                "NONE",
            )
        )

        if not environment_ready:

            run_status = (
                "ENVIRONMENT_SETUP_FAILED"
            )

        elif (
            stop_reason
            == "NO_TESTS_FOUND"
        ):

            run_status = (
                "NO_TESTS_FOUND"
            )

        elif (
            fix_verified
            and actual_applied_fixes
        ):

            run_status = (
                "FIX_VERIFIED"
            )

        elif (
            fix_verified
            and verification_mode
            == "STATIC_VERIFICATION"
        ):

            run_status = (
                "STATIC_VERIFICATION_PASSED"
            )

        elif fix_verified:

            run_status = (
                "TESTS_PASSED"
            )

        elif (
            stop_reason
            == "NO_ACTIONABLE_FIXES"
        ):

            run_status = (
                "NO_ACTIONABLE_FIXES"
            )

        elif (
            stop_reason
            == "RETRY_LIMIT_REACHED"
        ):

            run_status = (
                "RETRY_LIMIT_REACHED"
            )

        else:

            run_status = (
                "FAILED"
            )

        total_duration_seconds = (
            time.perf_counter()
            - run_started_at
        )

        score_result = (
            calculate_run_score(
                duration_seconds=(
                    total_duration_seconds
                ),
                applied_fixes=(
                    applied_fixes
                ),
                fix_verified=(
                    fix_verified
                ),
                git_result=(
                    git_result
                ),
                cicd_result=(
                    cicd_result
                ),
            )
        )

        # Static compile verification is useful,
        # but should not score exactly like a
        # real automated test suite.
        if (
            verification_mode
            == "STATIC_VERIFICATION"
            and fix_verified
        ):
            score_result[
                "verification_mode"
            ] = (
                "STATIC_VERIFICATION"
            )

        response_data = {
            "run_id":
                run_id,

            "user_id":
                user_id,

            "repository_url":
                str(
                    request.repository_url
                ),

            "team_name":
                request.team_name,

            "leader_name":
                request.leader_name,

            "branch_name":
                (
                    git_result.get(
                        "branch_name",
                        "",
                    )
                    if git_result
                    else ""
                ),

            "retry_limit":
                request.retry_limit,

            "status":
                run_status,

            "verification_mode":
                verification_mode,

            "duration_seconds":
                round(
                    total_duration_seconds,
                    2,
                ),

            "created_at":
                utc_now(),

            "progress":
                build_progress(
                    "COMPLETED",
                    (
                        "Repository analysis "
                        "completed."
                    ),
                ),

            "project":
                project_info,

            "repository": {
                "total_files_scanned":
                    len(
                        repository_files
                    ),
                "files":
                    repository_files,
            },

            "environment": {
                "ready":
                    environment_ready,
                "setup_results":
                    environment_setup_results,
            },

            "tests": {
                **test_discovery,

                "commands":
                    detected_test_commands,

                "execution_results":
                    verification_results,
            },

            "analysis": {
                "total_failures":
                    len(
                        detected_failures
                    ),
                "failures":
                    detected_failures,
            },

            "fix_application": {
                "total_applied":
                    len(
                        actual_applied_fixes
                    ),
                "applied_fixes":
                    applied_fixes,
            },

            "verification": {
                "passed":
                    fix_verified,

                "mode":
                    verification_mode,

                "results":
                    verification_results,
            },

            "iterations": {
                "used":
                    healing_result.get(
                        "iterations_used",
                        0,
                    ),

                "limit":
                    request.retry_limit,

                "timeline":
                    healing_result.get(
                        "timeline",
                        [],
                    ),
            },

            "score":
                score_result,

            "git":
                git_result,

            "pull_request":
                pull_request_result,

            "cicd":
                cicd_result,
        }

        results_file = (
            save_results(
                run_id=run_id,
                result_data=(
                    response_data
                ),
            )
        )

        response_data[
            "results_file"
        ] = results_file

        save_results(
            run_id=run_id,
            result_data=(
                response_data
            ),
        )

        save_run_db(
            response_data
        )

    except RunCancelledError:

        cancelled_data = (
            get_run_by_user_db(
                run_id=run_id,
                user_id=user_id,
            )
            or {}
        )

        cancelled_data.update(
            {
                "run_id":
                    run_id,

                "user_id":
                    user_id,

                "repository_url":
                    str(
                        request.repository_url
                    ),

                "team_name":
                    request.team_name,

                "leader_name":
                    request.leader_name,

                "retry_limit":
                    request.retry_limit,

                "status":
                    "CANCELLED",

                "progress":
                    build_progress(
                        "CANCELLED",
                        (
                            "Run cancelled "
                            "by user."
                        ),
                    ),

                "created_at":
                    cancelled_data.get(
                        "created_at"
                    )
                    or utc_now(),
            }
        )

        save_run_db(
            cancelled_data
        )

    except (
        RepositoryAgentError,
        ResultsServiceError,
    ) as error:

        failed_data = {
            "run_id":
                run_id,

            "user_id":
                user_id,

            "repository_url":
                str(
                    request.repository_url
                ),

            "team_name":
                request.team_name,

            "leader_name":
                request.leader_name,

            "retry_limit":
                request.retry_limit,

            "status":
                "FAILED",

            "progress":
                build_progress(
                    "FAILED",
                    str(error),
                ),

            "created_at":
                utc_now(),

            "error": {
                "type":
                    error.__class__.__name__,
                "message":
                    str(error),
            },
        }

        save_run_db(
            failed_data
        )

    except Exception as error:

        failed_data = {
            "run_id":
                run_id,

            "user_id":
                user_id,

            "repository_url":
                str(
                    request.repository_url
                ),

            "team_name":
                request.team_name,

            "leader_name":
                request.leader_name,

            "retry_limit":
                request.retry_limit,

            "status":
                "FAILED",

            "progress":
                build_progress(
                    "FAILED",
                    (
                        "Unexpected backend "
                        "failure."
                    ),
                ),

            "created_at":
                utc_now(),

            "error": {
                "type":
                    (
                        error
                        .__class__
                        .__name__
                    ),
                "message":
                    str(error),
            },
        }

        save_run_db(
            failed_data
        )

    finally:
        if repository_path:
            try:
                cleanup_repository_workspace(
                    run_id
                )
            except Exception:
                pass

        unregister_run_worker(
            run_id
        )


# ============================================================
# CANCEL RUN
# ============================================================

@app.post(
    "/api/runs/{run_id}/cancel"
)
def cancel_run(
    run_id: str,
    current_user: (
        AuthenticatedUser
    ) = Depends(
        get_current_user
    ),
):
    run_data = (
        get_run_by_user_db(
            run_id=run_id,
            user_id=(
                current_user.user_id
            ),
        )
    )

    if not run_data:
        raise HTTPException(
            status_code=404,
            detail="Run not found",
        )

    if run_data.get(
        "status"
    ) not in {
        "QUEUED",
        "RUNNING",
        "CANCELLING",
    }:
        raise HTTPException(
            status_code=409,
            detail=(
                "Run is already finished"
            ),
        )

    cancellation_event = (
        get_run_cancellation_event(
            run_id
        )
    )

    if not cancellation_event:
        raise HTTPException(
            status_code=409,
            detail=(
                "Run worker is no longer active"
            ),
        )

    cancellation_event.set()

    run_data[
        "status"
    ] = "CANCELLING"

    run_data[
        "progress"
    ] = build_progress(
        "CANCELLING",
        (
            "Cancellation requested."
        ),
    )

    save_run_db(
        run_data
    )

    try:
        create_audit_log(
            user_id=(
                current_user.user_id
            ),
            action=(
                "RUN_CANCELLED"
            ),
            entity_type="run",
            entity_id=run_id,
            details={
                "repository_url":
                    run_data.get(
                        "repository_url"
                    )
            },
        )
    except Exception:
        pass

    return {
        "run_id":
            run_id,
        "status":
            "CANCELLING",
    }


# ============================================================
# LIST RUNS
# ============================================================

@app.get("/api/runs")
def read_runs(
    page: int = Query(
        default=1,
        ge=1,
    ),
    page_size: int = Query(
        default=10,
        ge=1,
        le=100,
    ),
    status_filter: str | None = (
        Query(
            default=None
        )
    ),
    search_query: str | None = (
        Query(
            default=None
        )
    ),
    current_user: (
        AuthenticatedUser
    ) = Depends(
        get_current_user
    ),
):
    return list_runs_by_user_db(
        user_id=(
            current_user.user_id
        ),
        page=page,
        page_size=page_size,
        status_filter=(
            status_filter
        ),
        search_query=(
            search_query
        ),
    )


# ============================================================
# RUN DETAILS
# ============================================================

@app.get(
    "/api/runs/{run_id}"
)
def read_run(
    run_id: str,
    current_user: (
        AuthenticatedUser
    ) = Depends(
        get_current_user
    ),
):
    run_data = (
        get_run_by_user_db(
            run_id=run_id,
            user_id=(
                current_user.user_id
            ),
        )
    )

    if not run_data:
        raise HTTPException(
            status_code=404,
            detail="Run not found",
        )

    return run_data


# ============================================================
# RUN STATUS
# ============================================================

@app.get(
    "/api/runs/{run_id}/status"
)
def read_run_status(
    run_id: str,
    current_user: (
        AuthenticatedUser
    ) = Depends(
        get_current_user
    ),
):
    run_data = (
        get_run_by_user_db(
            run_id=run_id,
            user_id=(
                current_user.user_id
            ),
        )
    )

    if not run_data:
        raise HTTPException(
            status_code=404,
            detail="Run not found",
        )

    return {
        "run_id":
            run_id,

        "status":
            run_data.get(
                "status"
            ),

        "verification_mode":
            run_data.get(
                "verification_mode"
            ),

        "progress":
            run_data.get(
                "progress"
            ),

        "iterations":
            run_data.get(
                "iterations"
            ),

        "verification":
            run_data.get(
                "verification"
            ),

        "git":
            run_data.get(
                "git"
            ),

        "pull_request":
            run_data.get(
                "pull_request"
            ),

        "cicd":
            run_data.get(
                "cicd"
            ),

        "score":
            run_data.get(
                "score"
            ),

        "error":
            run_data.get(
                "error"
            ),
    }


# ============================================================
# RESULTS DOWNLOAD
# ============================================================

@app.get(
    "/api/runs/{run_id}/results/download"
)
def download_results(
    run_id: str,
    current_user: (
        AuthenticatedUser
    ) = Depends(
        get_current_user
    ),
):
    run_data = (
        get_run_by_user_db(
            run_id=run_id,
            user_id=(
                current_user.user_id
            ),
        )
    )

    if not run_data:
        raise HTTPException(
            status_code=404,
            detail="Run not found",
        )

    if run_data.get(
        "status"
    ) in {
        "QUEUED",
        "RUNNING",
        "CANCELLING",
    }:
        raise HTTPException(
            status_code=409,
            detail=(
                "Run is not completed yet"
            ),
        )

    try:
        pdf_file = (
            create_results_pdf(
                run_id=run_id,
                result_data=run_data,
            )
        )

    except PDFReportError as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        ) from error

    file_path = Path(
        pdf_file
    )

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail=(
                "Generated PDF was not found"
            ),
        )

    return FileResponse(
        path=file_path,
        media_type=(
            "application/pdf"
        ),
        filename=(
            f"{run_id}-results.pdf"
        ),
    )



# ============================================================
# RETRY RUN
# ============================================================

@app.post(
    "/api/runs/{run_id}/retry"
)
def retry_run(
    run_id: str,
    request: RunRetryRequest,
    current_user: (
        AuthenticatedUser
    ) = Depends(
        get_current_user
    ),
):
    previous_run = (
        get_run_by_user_db(
            run_id=run_id,
            user_id=(
                current_user.user_id
            ),
        )
    )

    if not previous_run:
        raise HTTPException(
            status_code=404,
            detail="Run not found",
        )

    if previous_run.get(
        "status"
    ) in {
        "QUEUED",
        "RUNNING",
        "CANCELLING",
    }:
        raise HTTPException(
            status_code=409,
            detail=(
                "Active run cannot be retried"
            ),
        )

    repository_url = (
        previous_run.get(
            "repository_url"
        )
    )

    team_name = (
        previous_run.get(
            "team_name"
        )
    )

    leader_name = (
        previous_run.get(
            "leader_name"
        )
    )

    retry_limit = (
        previous_run.get(
            "retry_limit",
            5,
        )
    )

    if (
        not repository_url
        or not team_name
        or not leader_name
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Previous run configuration "
                "is incomplete"
            ),
        )

    new_request = RunRequest(
        repository_url=(
            repository_url
        ),
        team_name=(
            team_name
        ),
        leader_name=(
            leader_name
        ),
        retry_limit=(
            retry_limit
        ),
        github_token=(
            request.github_token
        ),
    )

    new_run_id = str(
        uuid4()
    )

    initial_data = {
        "run_id":
            new_run_id,

        "user_id":
            current_user.user_id,

        "repository_url":
            repository_url,

        "team_name":
            team_name,

        "leader_name":
            leader_name,

        "retry_limit":
            retry_limit,

        "status":
            "QUEUED",

        "retry_of":
            run_id,

        "progress":
            build_progress(
                "QUEUED",
                (
                    "Retry run is "
                    "waiting to start."
                ),
            ),

        "created_at":
            utc_now(),
    }

    save_run_db(
        initial_data
    )

    cancellation_event = Event()

    worker = Thread(
        target=process_run,
        args=(
            new_request,
            new_run_id,
            current_user.user_id,
            cancellation_event,
        ),
        daemon=True,
    )

    register_run_worker(
        run_id=new_run_id,
        worker=worker,
        cancellation_event=(
            cancellation_event
        ),
    )

    worker.start()

    try:
        create_audit_log(
            user_id=(
                current_user.user_id
            ),
            action=(
                "RUN_RETRIED"
            ),
            entity_type="run",
            entity_id=(
                new_run_id
            ),
            details={
                "retry_of":
                    run_id,
                "repository_url":
                    repository_url,
            },
        )
    except Exception:
        pass

    return initial_data


# ============================================================
# DELETE RUN
# ============================================================

@app.delete(
    "/api/runs/{run_id}"
)
def delete_run(
    run_id: str,
    current_user: (
        AuthenticatedUser
    ) = Depends(
        get_current_user
    ),
):
    run_data = (
        get_run_by_user_db(
            run_id=run_id,
            user_id=(
                current_user.user_id
            ),
        )
    )

    if not run_data:
        raise HTTPException(
            status_code=404,
            detail="Run not found",
        )

    if run_data.get(
        "status"
    ) in {
        "QUEUED",
        "RUNNING",
        "CANCELLING",
    }:
        raise HTTPException(
            status_code=409,
            detail=(
                "Active run cannot be deleted"
            ),
        )

    results_file = (
        run_data.get(
            "results_file"
        )
    )

    try:
        delete_results(
            run_id
        )
    except ResultsServiceError:
        pass

    if (
        results_file
        and Path(
            results_file
        ).exists()
    ):
        try:
            Path(
                results_file
            ).unlink()
        except OSError:
            pass

    deleted = (
        delete_run_by_user_db(
            run_id=run_id,
            user_id=(
                current_user.user_id
            ),
        )
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Run not found",
        )

    try:
        create_audit_log(
            user_id=(
                current_user.user_id
            ),
            action=(
                "RUN_DELETED"
            ),
            entity_type="run",
            entity_id=run_id,
            details={
                "repository_url":
                    run_data.get(
                        "repository_url"
                    )
            },
        )
    except Exception:
        pass

    return {
        "run_id":
            run_id,
        "status":
            "DELETED",
    }


# ============================================================
# ANALYTICS
# ============================================================

@app.get(
    "/api/analytics"
)
def read_analytics(
    current_user: (
        AuthenticatedUser
    ) = Depends(
        get_current_user
    ),
):
    return (
        get_run_analytics_by_user_db(
            current_user.user_id
        )
    )


# ============================================================
# ACTIVITY
# ============================================================

@app.get(
    "/api/activity"
)
def read_activity(
    limit: int = Query(
        default=50,
        ge=1,
        le=100,
    ),
    current_user: (
        AuthenticatedUser
    ) = Depends(
        get_current_user
    ),
):
    activity = (
        list_audit_logs(
            user_id=(
                current_user.user_id
            ),
            limit=limit,
        )
    )

    return {
        "total":
            len(activity),
        "activity":
            activity,
    }