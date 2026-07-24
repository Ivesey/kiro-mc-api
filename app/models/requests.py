from typing import Literal

from pydantic import BaseModel, Field


class CreateCaseRequest(BaseModel):
    email: str = Field(
        ...,
        max_length=254,
        pattern=r"^[^@]+@[^@]+$",
        description="Email address of the user submitting the case.",
        examples=["user@example.com"],
    )
    issue: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Description of the problem reported by the user.",
        examples=["The dashboard fails to load after login."],
    )
    response: str = Field(
        default="",
        max_length=5000,
        description="Optional initial response (defaults to empty string).",
        examples=[""],
    )
    severity: Literal["low", "medium", "high", "critical"] = Field(
        ...,
        description="Urgency/impact level of the case.",
        examples=["high"],
    )


class UpdateCaseRequest(BaseModel):
    email: str = Field(
        ...,
        max_length=254,
        pattern=r"^[^@]+@[^@]+$",
        description="Email address of the user who submitted the case.",
        examples=["user@example.com"],
    )
    issue: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Description of the problem reported by the user.",
        examples=["The dashboard fails to load after login."],
    )
    response: str = Field(
        ...,
        max_length=5000,
        description="Support team reply or resolution for the case.",
        examples=["We have identified the issue and deployed a fix in v2.3.1."],
    )
    severity: Literal["low", "medium", "high", "critical"] = Field(
        ...,
        description="Urgency/impact level of the case.",
        examples=["high"],
    )
