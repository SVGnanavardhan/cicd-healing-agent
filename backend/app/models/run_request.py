from pydantic import (
    BaseModel,
    Field,
    HttpUrl,
    field_validator,
)


class RunRequest(
    BaseModel
):
    repository_url: HttpUrl

    team_name: str = Field(
        min_length=2,
        max_length=100,
    )

    leader_name: str = Field(
        min_length=2,
        max_length=100,
    )

    retry_limit: int = Field(
        default=5,
        ge=1,
        le=10,
    )

    github_token: str | None = Field(
        default=None,
        min_length=20,
        max_length=500,
        repr=False,
        exclude=True,
    )

    @field_validator(
        "team_name",
        "leader_name",
    )
    @classmethod
    def normalize_text(
        cls,
        value: str,
    ) -> str:
        cleaned_value = (
            value.strip()
        )

        if len(cleaned_value) < 2:
            raise ValueError(
                "Value must contain at least 2 non-space characters"
            )

        return cleaned_value

    @field_validator(
        "github_token",
        mode="before",
    )
    @classmethod
    def normalize_github_token(
        cls,
        value,
    ):
        if value is None:
            return None

        if not isinstance(
            value,
            str,
        ):
            return value

        cleaned_value = (
            value.strip()
        )

        if not cleaned_value:
            return None

        return cleaned_value