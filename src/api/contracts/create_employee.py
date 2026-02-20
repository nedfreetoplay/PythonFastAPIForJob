import datetime

from pydantic import BaseModel, field_validator, Field

from src.core.models.employee import FULLNAME_MAX_LENGTH, POSITION_MAX_LENGTH


class CreateEmployee(BaseModel):
    full_name: str = Field(..., max_length=FULLNAME_MAX_LENGTH)
    position: str = Field(..., max_length=POSITION_MAX_LENGTH)
    hired_at: datetime.date | None

    @field_validator('full_name', 'position', mode='before')
    @classmethod
    def strip_strings(cls, v):
        if isinstance(v, str):
            return v.strip()
        return v


class ResponseCreateEmployee(BaseModel):
    id: int
    department_id: int
    full_name: str
    position: str
    hired_at: datetime.date | None
    created_at: datetime.datetime