from fastapi import Depends

from src.application.services.departments_service import DepartmentsService
from src.application.services.employees_service import EmployeesService
from src.core.abstractions.departments_service_protocol import DepartmentsServiceProtocol
from src.core.abstractions.employees_service_protocol import EmployeesServiceProtocol
from src.data_access.context import DbContext, get_db_context


def get_departments_service(
    db: DbContext = Depends(get_db_context)
) -> DepartmentsServiceProtocol:
    return DepartmentsService(db=db)

def get_employees_service(
    db: DbContext = Depends(get_db_context)
) -> EmployeesServiceProtocol:
    return EmployeesService(db=db)
