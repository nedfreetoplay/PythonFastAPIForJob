from typing import Literal

from pydantic import BaseModel, Field, model_validator


class DepartmentDeleteRequest(BaseModel):
    mode: Literal["cascade", "reassign"] = Field(
        ...,
        description="Режим удаления подразделения"
    )
    reassign_to_department_id: int | None = Field(
        None,
        description="ID подразделения для перевода сотрудников (обязательно при mode=reassign)",
        gt=0
    )

    @model_validator(mode='after')
    def check_reassign_department_id(self):
        if self.mode == "reassign" and self.reassign_to_department_id is None:
            raise ValueError(
                'Поле reassign_to_department_id обязательно при mode="reassign"'
            )
        if self.mode == "cascade" and self.reassign_to_department_id is not None:
            raise ValueError(
                'Поле reassign_to_department_id должно быть пустым при mode="cascade"'
            )
        return self