from typing import List

from pydantic import BaseModel, model_validator

from src.core.models.department import ReadDepartment
from src.core.models.employee import ReadEmployee


class DepartmentGetRequest(BaseModel):
    depth: int
    include_employees: bool = True

    @model_validator(mode='after')
    def check_depth(self):
        if 0 <= self.depth < 6:
            raise ValueError(
                'Поле depth не может быть меньше 0 или больше 5'
            )
        return self


class DepartmentGetResponse(BaseModel):
    department: ReadDepartment     # объект подразделения
    employees: List[ReadEmployee]  # если include_employees=true, сортировка по created_at или full_name)
    children: List[ReadDepartment] # вложенные подразделения до depth, рекурсивно

    #TODO: Нужна функция сортировки для employees.
    # В зависимости от внешнего параметра include_employees, сортировать по полю created_at или full_name