from pydantic import BaseModel, Field


class RunRetryRequest(BaseModel):
    github_token: str | None = Field(
        default=None,
        min_length=20,
        max_length=500,
        repr=False,
        exclude=True,
    )