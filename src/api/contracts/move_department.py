import datetime

from pydantic import BaseModel, field_validator


class MoveDepartment(BaseModel):
    name: str | None = None
    parent_id: int | None = None

    @field_validator('name', mode='before')
    @classmethod
    def strip_strings(cls, v):
        if isinstance(v, str):
            return v.strip()
        return v


class ResponseMoveDepartment(BaseModel):
    id: int
    name: str
    parent_id: int | None
    created_at: datetime.datetime