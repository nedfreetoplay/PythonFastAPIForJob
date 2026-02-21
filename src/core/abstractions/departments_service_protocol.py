from enum import Enum
from typing import Protocol, List

from src.core.models.department import CreateDepartment, ReadDepartment, UpdateDepartment

class DeleteMode(str, Enum):
    CASCADE =  "cascade"
    REASSIGN = "reassign"

class DepartmentsServiceProtocol(Protocol):
    async def create_department(self, department: CreateDepartment) -> ReadDepartment:
        ...

    async def get_department(self, department_id: int) -> ReadDepartment:
        ...

    async def get_department_children(self, department_id: int) -> List[ReadDepartment]:
        ...

    async def update_department(self, depart: UpdateDepartment) -> ReadDepartment:
        ...

    async def delete_department(self, department_id: int, mode: DeleteMode, reassign_to_department_id: int | None) -> str:
        ...