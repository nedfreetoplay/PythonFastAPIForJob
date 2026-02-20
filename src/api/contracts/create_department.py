import datetime

from pydantic import BaseModel, Field, field_validator

from src.core.models.department import NAME_MAX_LENGTH


class CreateDepartment(BaseModel):
    name: str = Field(..., max_length=NAME_MAX_LENGTH)
    parent_id: int | None = None

    @field_validator('name', mode='before')
    @classmethod
    def strip_strings(cls, v):
        if isinstance(v, str):
            return v.strip()
        return v


class ResponseCreateDepartment(BaseModel):
    id: int
    name: str
    parent_id: int | None
    created_at: datetime.datetime