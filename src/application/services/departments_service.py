from typing import List

from src.core.abstractions.departments_service_protocol import DepartmentsServiceProtocol, DeleteMode
from src.core.models.department import CreateDepartment, ReadDepartment, UpdateDepartment
from src.data_access.context import DbContext


class DepartmentsService(DepartmentsServiceProtocol):

    def __init__(self, db: DbContext):
        self.db = db

    async def create_department(self, department: CreateDepartment) -> ReadDepartment:
        return await self.db.department.add(department)

    async def get_department(self, department_id: int) -> ReadDepartment:
        return await self.db.department.get_by_id(department_id)

    async def get_department_children(self, department_id: int) -> List[ReadDepartment]:
        return await self.db.department.get_children(department_id)

    async def update_department(self, depart: UpdateDepartment) -> ReadDepartment:
        return await self.db.department.update(depart)

    async def delete_department(self, department_id: int, mode: DeleteMode, reassign_to_department_id: int | None) -> str:

        errors: List[str] = []
        result = None

        if mode == DeleteMode.REASSIGN:
            if reassign_to_department_id is None:
                errors.append("reassign_to_department_id cannot be None")
            is_exists = await self.db.department.is_exists(department_id)
            if is_exists is None:
                errors.append("department with id {} does not exist".format(department_id))

            # Меняем у сотрудников подразделение
            employees = await self.db.employee.get_all_employees_into_department(department_id)
            for employee in employees:
                employee.department_id = reassign_to_department_id

            # Удаляем ненужное нам подразделение
            result = await self.db.department.delete_without_cascade(department_id)

        elif mode == DeleteMode.CASCADE:
            result = await self.db.department.delete_with_cascade(department_id)

        if result is not None and result == False:
            errors.append("couldn't delete Department, id {}".format(department_id))

        errors_str = '\n'.join(errors)
        return errors_str








