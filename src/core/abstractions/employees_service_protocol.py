from typing import Protocol, List

from src.core.models.employee import ReadEmployee, CreateEmployee


class EmployeesServiceProtocol(Protocol):

    async def create_employee(self, employee: CreateEmployee) -> ReadEmployee:
        ...

    async def get_all_employees_into_department(self, department_id: int) -> List[ReadEmployee]:
        ...
