from src.core.models.employee import CreateEmployee, ReadEmployee
from src.data_access.context import DbContext


class EmployeesService:

    def __init__(self, db: DbContext):
        self.db = db

    async def create_employee(self, employee: CreateEmployee) -> ReadEmployee:
        return await self.db.employee.add(employee)
