from enum import Enum
from typing import List

from src.core.models.department import CreateDepartment, ReadDepartment, create_department
from src.data_access.context import DbContext


class DeleteMode(str, Enum):
    CASCADE =  "cascade"
    REASSIGN = "reassign"


class DepartmentsService:

    def __init__(self, db: DbContext):
        self.db = db

    async def create_department(self, department: CreateDepartment) -> ReadDepartment:
        return await self.db.department.add(department)

    async def get_department(self, department_id: int) -> ReadDepartment:
        return await self.db.department.get_by_id(department_id)

    async def update_department(self, department_id: int, department_name: str | None, parent_id: int | None) -> ReadDepartment:

        # Меняем название, но названием не может быть None, так что проверяем что мы хотим изменить название.
        if department_name is not None:
            await self.db.department.set_name(department_id, department_name)

        # Нам все равно изменился ли parent у подразделения.
        await self.db.department.set_parent_id(department_id, parent_id)

        return await self.db.department.get_by_id(department_id)

    async def delete_department(
        self,
        department_id: int,
        mode: DeleteMode,
        reassign_to_department_id: int | None
    ) -> str:

        errors: List[str] = []

        if mode == DeleteMode.REASSIGN:
            if reassign_to_department_id is None:
                errors.append("if mode == REASSIGN then reassign_to_department_id cannot be None")
            is_exists = await self.db.department.get_by_id(department_id)
            if is_exists is None:
                errors.append("department with id {} does not exist".format(department_id))
        elif mode == DeleteMode.CASCADE:
            pass
        # list_employees = await self.db.employee.get_all_employees_into_department(department_id)
            #TODO: Продолжить!
        # Удаляем подразделение
        await self.db.department.delete(department_id)

        return ''