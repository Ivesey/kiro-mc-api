import uuid
from typing import Literal

from pydantic import BaseModel, Field


class CaseModel(BaseModel):
    case_id: uuid.UUID = Field(
        ...,
        description="Unique identifier for the support case (RFC 4122 UUID).",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    email: str = Field(
        ...,
        max_length=254,
        pattern=r"^[^@]+@[^@]+$",
        description="Email address of the user who submitted the case (RFC 5321, max 254 chars).",
        examples=["user@example.com"],
    )
    issue: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Description of the problem reported by the user (1–2000 characters).",
        examples=["The dashboard fails to load after login."],
    )
    response: str = Field(
        ...,
        max_length=5000,
        description="Support team reply or resolution for the case (max 5000 characters).",
        examples=["We have identified the issue and deployed a fix in v2.3.1."],
    )
    severity: Literal["low", "medium", "high", "critical"] = Field(
        ...,
        description="Urgency/impact level of the case.",
        examples=["high"],
    )
