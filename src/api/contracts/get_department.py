from typing import List

from pydantic import BaseModel

from src.core.models.department import ReadDepartment
from src.core.models.employee import ReadEmployee


class DepartmentGetResponse(BaseModel):
    department: ReadDepartment     # объект подразделения
    employees: List[ReadEmployee]  # если include_employees=true, сортировка по created_at или full_name)
    children: List[ReadDepartment] # вложенные подразделения до depth, рекурсивно
