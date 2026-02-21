from typing import Optional, List, Dict, Set
from datetime import datetime

from src.core.abstractions.department_repo_protocol import DepartmentRepositoryProtocol
from src.core.abstractions.employee_repo_protocol import EmployeeRepositoryProtocol
from src.core.models.department import CreateDepartment, ReadDepartment, UpdateDepartment
from src.core.models.employee import CreateEmployee, ReadEmployee
from src.core.abstractions.departments_service_protocol import DeleteMode, DepartmentsServiceProtocol
from src.core.abstractions.employees_service_protocol import EmployeesServiceProtocol


# ==============================================================================
# FAKE REPOSITORIES (Хранилища данных в памяти)
# ==============================================================================

class FakeDepartmentRepository(DepartmentRepositoryProtocol):
    """In-memory реализация репозитория департаментов для тестов"""

    def __init__(self):
        self._departments: Dict[int, ReadDepartment] = {}
        self._next_id: int = 1

    async def add(self, department: CreateDepartment) -> ReadDepartment:
        dept_id = self._next_id
        self._next_id += 1

        read_dept = ReadDepartment(
            id=dept_id,
            name=department.name,
            parent_id=department.parent_id,
            created_at=datetime.now(),
        )
        self._departments[dept_id] = read_dept
        return read_dept

    async def get_by_id(self, department_id: int) -> Optional[ReadDepartment]:
        return self._departments.get(department_id)

    async def get_children(self, department_id: int) -> List[ReadDepartment]:
        return [d for d in self._departments.values() if d.parent_id == department_id]

    async def is_exists(self, department_id: int) -> bool:
        return department_id in self._departments

    async def get_all_descendants_ids(self, department_id: int) -> Set[int]:
        """Рекурсивный сбор всех потомков"""
        descendants = set()
        children = await self.get_children(department_id)
        for child in children:
            descendants.add(child.id)
            descendants.update(await self.get_all_descendants_ids(child.id))
        return descendants

    async def has_cycle(self, department_id: int | None, new_parent_id: int | None) -> bool:
        """Проверка на цикл: новый родитель не должен быть потомком текущего департамента"""
        if new_parent_id is None:
            return False
        if department_id is None:
            return False
        if new_parent_id == department_id:
            return True
        descendants = await self.get_all_descendants_ids(department_id)
        return new_parent_id in descendants

    async def update(self, department_id: int, update_dto: UpdateDepartment) -> ReadDepartment:
        if department_id not in self._departments:
            raise ValueError(f"Department {department_id} not found")

        existing = self._departments[department_id]
        updated = ReadDepartment(
            id=existing.id,
            name=update_dto.name if update_dto.name is not None and update_dto.name != existing.name else existing.name,
            parent_id=update_dto.parent_id if update_dto.parent_id != existing.parent_id else existing.parent_id,
            created_at=existing.created_at,
        )
        self._departments[department_id] = updated
        return updated

    async def delete_with_cascade(self, department_id: int) -> bool:
        if department_id not in self._departments:
            return False
        descendants = await self.get_all_descendants_ids(department_id)
        for desc_id in descendants:
            self._departments.pop(desc_id, None)
        self._departments.pop(department_id, None)
        return True

    async def delete_without_cascade(self, department_id: int) -> bool:
        if department_id not in self._departments:
            return False
        self._departments.pop(department_id, None)
        return True

    # --- Helper methods for tests ---
    def clear(self):
        self._departments.clear()
        self._next_id = 1

    def seed(self, departments: List[ReadDepartment]):
        for dept in departments:
            self._departments[dept.id] = dept
            if dept.id >= self._next_id:
                self._next_id = dept.id + 1


class FakeEmployeeRepository(EmployeeRepositoryProtocol):
    """In-memory реализация репозитория сотрудников для тестов"""

    def __init__(self):
        self._employees: Dict[int, ReadEmployee] = {}
        self._next_id: int = 1

    async def add(self, employee: CreateEmployee) -> ReadEmployee:
        # Проверка существования подразделения происходит в сервисе.

        emp_id = self._next_id
        self._next_id += 1

        read_emp = ReadEmployee(
            id=emp_id,
            department_id=employee.department_id,
            full_name=employee.full_name,
            position=employee.position,
            hired_at=employee.hired_at,
            created_at=datetime.now(),
        )
        self._employees[emp_id] = read_emp
        return read_emp

    async def get_by_id(self, employee_id: int) -> Optional[ReadEmployee]:
        return self._employees.get(employee_id)

    async def get_all_employees_into_department(self, department_id: int) -> List[ReadEmployee]:
        return [e for e in self._employees.values() if e.department_id == department_id]

    async def is_exists(self, employee_id: int) -> bool:
        return employee_id in self._employees

    async def delete(self, employee_id: int) -> bool:
        if employee_id in self._employees:
            del self._employees[employee_id]
            return True
        return False

    # --- Helper methods for tests ---
    def clear(self):
        self._employees.clear()
        self._next_id = 1

    def seed(self, employees: List[ReadEmployee]):
        for emp in employees:
            self._employees[emp.id] = emp
            if emp.id >= self._next_id:
                self._next_id = emp.id + 1

    async def reassign_employees(self, from_department_id: int, to_department_id: int):
        """Перевод сотрудников из одного департамента в другой (для режима reassign)"""
        for emp in self._employees.values():
            if emp.department_id == from_department_id:
                emp.department_id = to_department_id


# ==============================================================================
# FAKE SERVICES (Бизнес-логика в памяти)
# ==============================================================================

class FakeDepartmentsService(DepartmentsServiceProtocol):
    """In-memory реализация сервиса департаментов"""

    def __init__(
        self,
        depart_repository: Optional[FakeDepartmentRepository] = None,
        employee_repository: Optional[FakeEmployeeRepository] = None,
    ):
        self._repo = depart_repository or FakeDepartmentRepository()
        self._empl_repo = employee_repository or FakeEmployeeRepository()

    async def create_department(self, department: CreateDepartment) -> ReadDepartment:
        # Проверка на цикл
        if await self._repo.has_cycle(None, department.parent_id):
            raise ValueError("Cannot create department: would create a cycle")
        return await self._repo.add(department)

    async def get_department(self, department_id: int) -> Optional[ReadDepartment]:
        return await self._repo.get_by_id(department_id)

    async def get_department_children(self, department_id: int) -> List[ReadDepartment]:
        return await self._repo.get_children(department_id)

    async def update_department(self, department_id: int, update_dto: UpdateDepartment) -> ReadDepartment:
        # Проверка на цикл при перемещении
        if await self._repo.has_cycle(department_id, update_dto.parent_id):
            raise ValueError("Cannot move department: would create a cycle")
        return await self._repo.update(department_id, update_dto)

    async def delete_department(self, department_id: int, mode: DeleteMode, reassign_to_department_id: int | None) -> str:
        errors = []

        # Проверка существования
        if not await self._repo.is_exists(department_id):
            errors.append(f"Department {department_id} not found")

            errors_str = '\n'.join(errors)
            return errors_str

        if mode == DeleteMode.CASCADE:
            await self._repo.delete_with_cascade(department_id)
        elif mode == DeleteMode.REASSIGN:
            if reassign_to_department_id is None:
                errors.append("reassign_to_department_id is required for REASSIGN mode")

                errors_str = '\n'.join(errors)
                return errors_str
            if not await self._repo.is_exists(reassign_to_department_id):
                errors.append(f"Reassign target department {reassign_to_department_id} not found")

                errors_str = '\n'.join(errors)
                return errors_str

            # Сначала переводим сотрудников
            await self._empl_repo.reassign_employees(department_id, reassign_to_department_id)

            # Удаляем подразделение
            await self._repo.delete_without_cascade(department_id)

        errors_str = '\n'.join(errors)
        return errors_str

    # --- Helper for tests ---
    @property
    def repository(self) -> FakeDepartmentRepository:
        return self._repo


class FakeEmployeesService(EmployeesServiceProtocol):
    """In-memory реализация сервиса сотрудников"""

    def __init__(
        self,
        repository: Optional[FakeEmployeeRepository] = None,
        depart_repository: Optional[FakeDepartmentRepository] = None,
    ):
        self._repo = repository or FakeEmployeeRepository()
        self._depart_repo = depart_repository or FakeDepartmentRepository()

    async def create_employee(self, employee: CreateEmployee) -> ReadEmployee:
        is_exist = await self._depart_repo.is_exists(employee.department_id)
        if not is_exist:
            raise ValueError("There is no such Department.")

        # Валидация
        if not employee.full_name or len(employee.full_name.strip()) == 0:
            raise ValueError("Full name is required")

        return await self._repo.add(employee)

    async def get_all_employees_into_department(self, department_id: int) -> List[ReadEmployee]:
        return await self._repo.get_all_employees_into_department(department_id)

    # --- Helper for tests ---
    @property
    def repository(self) -> FakeEmployeeRepository:
        return self._repo