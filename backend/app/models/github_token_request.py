from pydantic import (
    BaseModel,
    Field,
)


class GitHubTokenRequest(
    BaseModel
):
    github_token: str = Field(
        min_length=20,
        max_length=500,
        repr=False,
        exclude=True,
    )