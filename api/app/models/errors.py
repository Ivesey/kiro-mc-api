from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    detail: str = Field(..., max_length=500)
