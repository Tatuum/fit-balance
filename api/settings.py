from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode


class Settings(BaseSettings):
    """Environment configuration. Field `x` is read from the variable `X`."""

    # NoDecode: take the raw string (comma-separated), not JSON — the AWS CLI's
    # `Variables={...}` shorthand can't carry a JSON list.
    allowed_origins: Annotated[list[str], NoDecode] = [
        "http://localhost:5173",  # Vite's default dev-server ports
        "http://127.0.0.1:5173",
    ]

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def _split_commas(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value
