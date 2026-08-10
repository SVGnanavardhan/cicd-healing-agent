import os
from dataclasses import dataclass
from typing import Any

import requests
from dotenv import load_dotenv
from fastapi import (
    Depends,
    HTTPException,
    status,
)
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)


load_dotenv()


security = HTTPBearer(
    auto_error=False
)


@dataclass(frozen=True)
class AuthenticatedUser:
    user_id: str
    email: str | None
    claims: dict[str, Any]


def get_supabase_config() -> tuple[
    str,
    str,
]:
    supabase_url = (
        os.getenv(
            "SUPABASE_URL",
            "",
        )
        .strip()
        .rstrip("/")
    )

    supabase_key = (
        os.getenv(
            "SUPABASE_PUBLISHABLE_KEY"
        )
        or os.getenv(
            "SUPABASE_ANON_KEY"
        )
        or ""
    ).strip()

    if (
        not supabase_url
        or not supabase_key
    ):
        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "Supabase backend configuration "
                "is missing"
            ),
        )

    return (
        supabase_url,
        supabase_key,
    )


def verify_supabase_access_token(
    access_token: str,
) -> AuthenticatedUser:
    token = (
        access_token
        or ""
    ).strip()

    if not token:
        raise HTTPException(
            status_code=(
                status.HTTP_401_UNAUTHORIZED
            ),
            detail=(
                "Authentication token is missing"
            ),
        )

    (
        supabase_url,
        supabase_key,
    ) = get_supabase_config()

    user_endpoint = (
        f"{supabase_url}/auth/v1/user"
    )

    try:
        response = requests.get(
            user_endpoint,
            headers={
                "apikey": supabase_key,
                "Authorization": (
                    f"Bearer {token}"
                ),
            },
            timeout=15,
        )

    except requests.Timeout as error:
        raise HTTPException(
            status_code=(
                status.HTTP_504_GATEWAY_TIMEOUT
            ),
            detail=(
                "Authentication service timed out"
            ),
        ) from error

    except requests.RequestException as error:
        raise HTTPException(
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail=(
                "Authentication service unavailable"
            ),
        ) from error

    if response.status_code in {
        400,
        401,
        403,
    }:
        raise HTTPException(
            status_code=(
                status.HTTP_401_UNAUTHORIZED
            ),
            detail=(
                "Invalid or expired access token"
            ),
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail=(
                "Unable to verify authentication"
            ),
        )

    try:
        user_data = (
            response.json()
        )

    except ValueError as error:
        raise HTTPException(
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail=(
                "Invalid authentication response"
            ),
        ) from error

    user_id = (
        user_data.get("id")
    )

    if (
        not isinstance(
            user_id,
            str,
        )
        or not user_id.strip()
    ):
        raise HTTPException(
            status_code=(
                status.HTTP_401_UNAUTHORIZED
            ),
            detail=(
                "Invalid authenticated user"
            ),
        )

    email = (
        user_data.get(
            "email"
        )
    )

    return AuthenticatedUser(
        user_id=user_id.strip(),
        email=(
            email
            if isinstance(
                email,
                str,
            )
            else None
        ),
        claims=user_data,
    )


def get_current_user(
    credentials: (
        HTTPAuthorizationCredentials
        | None
    ) = Depends(
        security
    ),
) -> AuthenticatedUser:
    if credentials is None:
        raise HTTPException(
            status_code=(
                status.HTTP_401_UNAUTHORIZED
            ),
            detail=(
                "Authentication required"
            ),
        )

    scheme = (
        credentials.scheme
        or ""
    ).lower()

    if scheme != "bearer":
        raise HTTPException(
            status_code=(
                status.HTTP_401_UNAUTHORIZED
            ),
            detail=(
                "Bearer authentication required"
            ),
        )

    return (
        verify_supabase_access_token(
            credentials.credentials
        )
    )