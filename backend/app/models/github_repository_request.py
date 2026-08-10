from pydantic import (
    BaseModel,
    Field,
    HttpUrl,
)


class GitHubRepositoryRequest(
    BaseModel
):
    repository_url: HttpUrl

    github_token: str = Field(
        min_length=20,
        max_length=500,
        repr=False,
        exclude=True,
    )