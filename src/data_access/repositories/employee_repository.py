from typing import Optional, List

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.abstractions.employee_repo_protocol import EmployeeRepositoryProtocol
from src.core.models.employee import CreateEmployee, ReadEmployee
from src.data_access.entities.entities import Department, Employee


class EmployeeRepository(EmployeeRepositoryProtocol):
    """Репозиторий для работы с сотрудниками"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, employee: CreateEmployee) -> ReadEmployee:
        # В принципе можно убрать проверку на существование подразделения
        #  перед добавлением.

        result = await self.session.execute(
            select(Department).where(Department.id == employee.department_id)
        )
        if result is None:
            raise ValueError("There is no such Department.")

        new_employee = Employee(
            department_id = employee.department_id,
            full_name = employee.full_name,
            position = employee.position,
            hired_at = employee.hired_at,
        )

        self.session.add(new_employee)
        await self.session.flush() # Получаем ID без коммита
        await self.session.refresh(new_employee)

        created_employee = ReadEmployee(
            id = new_employee.id,
            department_id = new_employee.department_id,
            full_name = new_employee.full_name,
            position = new_employee.position,
            hired_at = new_employee.hired_at,
            created_at = new_employee.created_at,
        )

        return created_employee

    async def get_by_id(self, employee_id: int) -> Optional[ReadEmployee]:
        result = await self.session.execute(
            select(Employee).where(Employee.id == employee_id)
        )
        employee = result.scalar_one_or_none()
        if not employee:
            return None

        read_employee = ReadEmployee(
            id = employee.id,
            department_id = employee.department_id,
            full_name = employee.full_name,
            position = employee.position,
            hired_at = employee.hired_at,
            created_at = employee.created_at,
        )

        return read_employee

    async def get_all_employees_into_department(self, department_id: int) -> list[ReadEmployee]:
        result = await self.session.execute(
            select(Employee).where(Employee.department_id == department_id)
        )
        employees = result.scalars()

        list_employees: List[ReadEmployee] = []

        for employee in employees:
            read_employee = ReadEmployee(
                id = employee.id,
                department_id = employee.department_id,
                full_name = employee.full_name,
                position = employee.position,
                hired_at = employee.hired_at,
                created_at = employee.created_at,
            )

            list_employees.append(read_employee)

        return list_employees

    async def is_exists(self, employee_id: int) -> bool:
        result = await self.session.execute(
            select(Employee).where(Employee.id == employee_id)
        )
        return result.scalar_one_or_none() is not None

    async def delete(self, employee_id: int) -> bool:
        stmt = delete(Employee).where(Employee.id == employee_id)
        result = await self.session.execute(stmt)
        return result.rowcount > 0
