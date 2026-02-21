from typing import List

from src.core.abstractions.employees_service_protocol import EmployeesServiceProtocol
from src.core.models.employee import CreateEmployee, ReadEmployee
from src.data_access.context import DbContext


class EmployeesService(EmployeesServiceProtocol):

    def __init__(self, db: DbContext):
        self.db = db

    async def create_employee(self, employee: CreateEmployee) -> ReadEmployee:
        # Проверяем существует ли подразделение в которые добавим сотрудника
        is_exist = await self.db.department.is_exists(employee.department_id)
        if not is_exist:
            raise ValueError("There is no such Department.")

        # Валидация происходит в момент создания CreateEmployee

        return await self.db.employee.add(employee)

    async def get_all_employees_into_department(self, department_id: int) -> List[ReadEmployee]:
        return await self.db.employee.get_all_employees_into_department(department_id)
