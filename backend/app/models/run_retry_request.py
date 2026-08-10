from pydantic import (
    BaseModel,
    Field,
    field_validator,
)


class RunRetryRequest(
    BaseModel
):
    github_token: str | None = Field(
        default=None,
        min_length=20,
        max_length=500,
        repr=False,
        exclude=True,
    )

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