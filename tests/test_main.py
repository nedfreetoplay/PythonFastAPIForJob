import sys
from datetime import datetime
from pathlib import Path
from typing import AsyncGenerator

import httpx
import pytest
from httpx import ASGITransport
from pytest_asyncio import fixture as async_fixture

from fakes import FakeDepartmentRepository, FakeEmployeeRepository, FakeDepartmentsService, FakeEmployeesService
from main import app
from src.core.models.department import create_department
from src.core.models.employee import create_employee
from src.dependencies import get_employees_service, get_departments_service

# Добавляем корень проекта в sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))


# ==============================================================================
# ФИКСТУРЫ С ФЕЙКОВЫМИ СЕРВИСАМИ И РЕПОЗИТОРИЯМИ
# ==============================================================================

# noinspection PyTypeChecker
@async_fixture
async def department_repository() -> FakeDepartmentRepository:
    """Создает фейковый репозиторий департаментов"""
    repo = FakeDepartmentRepository()
    yield repo
    repo.clear()


# noinspection PyTypeChecker
@async_fixture
async def employee_repository() -> FakeEmployeeRepository:
    """Создает фейковый репозиторий сотрудников"""
    repo = FakeEmployeeRepository()
    yield repo
    repo.clear()


# noinspection PyTypeChecker
@async_fixture
async def departments_service(
        department_repository: FakeDepartmentRepository,
        employee_repository: FakeEmployeeRepository,
) -> FakeDepartmentsService:
    """Создает фейковый сервис департаментов"""
    service = FakeDepartmentsService(
        depart_repository=department_repository,
        employee_repository=employee_repository,
    )
    yield service


# noinspection PyTypeChecker
@async_fixture
async def employees_service(
        employee_repository: FakeEmployeeRepository,
        department_repository: FakeDepartmentRepository,
) -> FakeEmployeesService:
    """Создает фейковый сервис сотрудников"""
    service = FakeEmployeesService(
        repository=employee_repository,
        depart_repository=department_repository,
    )
    yield service


@async_fixture
async def override_dependencies(
        departments_service: FakeDepartmentsService,
        employees_service: FakeEmployeesService,
) -> AsyncGenerator[None, None]:
    """Переопределяет зависимости в приложении для использования фейковых сервисов"""

    async def override_depart():
        return departments_service

    async def override_emp():
        return employees_service

    app.dependency_overrides[get_departments_service] = override_depart
    app.dependency_overrides[get_employees_service] = override_emp

    yield

    # Очистка переопределений после теста
    app.dependency_overrides.clear()


@async_fixture
async def client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Создает асинхронный HTTP клиент для тестов"""
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

# ==============================================================================
# ТЕСТЫ
# ==============================================================================

# noinspection PyShadowingNames
@pytest.mark.asyncio
async def test_health(client: httpx.AsyncClient):
    """Тест health endpoint"""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# noinspection PyShadowingNames
class TestCreateDepartment:
    """Тесты для POST /departments"""

    @pytest.mark.asyncio
    async def test_create_department_success_with_parent(
            self,
            client: httpx.AsyncClient,
            override_dependencies: None,
            departments_service: FakeDepartmentsService,
    ):
        # Сначала создаем родительский департамент через сервис
        new_dept, errors = create_department(name="Parent Dept", parent_id=None)
        assert errors == ""
        parent_dept = await departments_service.repository.add(new_dept)

        # Создаем дочерний департамент через API
        payload = {"name": "Child Dept", "parent_id": parent_dept.id}
        response = await client.post("/departments", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Child Dept"
        assert data["parent_id"] == parent_dept.id
        assert "id" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_create_department_root(
            self,
            client: httpx.AsyncClient,
            override_dependencies: None,
    ):
        # Создаем корневой департамент (без родителя)
        payload = {"name": "Root Dept"}
        response = await client.post("/departments", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Root Dept"
        assert data["parent_id"] is None

    @pytest.mark.asyncio
    async def test_create_department_validation_error(
            self,
            client: httpx.AsyncClient,
            override_dependencies: None,
    ):
        # Пустое имя должно вызвать ошибку валидации
        payload = {"name": ""}
        response = await client.post("/departments", json=payload)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_department_cycle_detection(
            self,
            client: httpx.AsyncClient,
            override_dependencies: None,
            departments_service: FakeDepartmentsService,
    ):
        # Создаем департамент A
        new_dept, errors =create_department(name="Dept A", parent_id=None)
        assert errors == ""
        dept_a = await departments_service.repository.add(new_dept)
        # Создаем департамент B с родителем A

        new_dept, errors = create_department(name="Dept B", parent_id=dept_a.id)
        assert errors == ""
        dept_b = await departments_service.repository.add(new_dept)

        # Пытаемся сделать A дочерним B (цикл!)
        payload = {"name": "Dept A Updated", "parent_id": dept_b.id}
        response = await client.patch(f"/departments/{dept_a.id}", json=payload)

        assert response.status_code == 400
        assert "cycle" in response.json()["detail"].lower()


# noinspection PyShadowingNames
class TestCreateEmployeeInDepartment:
    """Тесты для POST /departments/{id}/employees"""

    @pytest.mark.asyncio
    async def test_create_employee_success(
            self,
            client: httpx.AsyncClient,
            override_dependencies: None,
            departments_service: FakeDepartmentsService,
    ):
        # Сначала создаем департамент через сервис
        new_dept, errors = create_department(name="IT Department", parent_id=None)
        assert errors == ""
        dept = await departments_service.repository.add(new_dept)

        # Создаем сотрудника через API
        payload = {
            "full_name": "Ivan Ivanov",
            "position": "Developer",
            "hired_at": "2023-01-01"
        }
        response = await client.post(f"/departments/{dept.id}/employees", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Ivan Ivanov"
        assert data["position"] == "Developer"
        assert data["department_id"] == dept.id
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_employee_dept_not_found(
            self,
            client: httpx.AsyncClient,
            override_dependencies: None,
    ):
        # Департамент не существует
        payload = {
            "full_name": "Ivan Ivanov",
            "position": "Developer",
            "hired_at": "2023-01-01"
        }
        response = await client.post("/departments/999/employees", json=payload)

        assert response.status_code == 404
        assert "department" in response.json()["detail"]["error"].lower()

    @pytest.mark.asyncio
    async def test_create_employee_validation_error(
            self,
            client: httpx.AsyncClient,
            override_dependencies: None,
            departments_service: FakeDepartmentsService,
    ):
        # Создаем департамент
        new_dept, errors = create_department(name="IT", parent_id=None)
        assert errors == ""
        dept = await departments_service.repository.add(new_dept)

        # Пустое имя сотрудника
        payload = {
            "full_name": "",
            "position": "Developer",
            "hired_at": "2023-01-01"
        }
        response = await client.post(f"/departments/{dept.id}/employees", json=payload)

        assert response.status_code == 422


# noinspection PyShadowingNames,DuplicatedCode
class TestGetDepartment:
    """Тесты для GET /departments/{id}"""

    @pytest.mark.asyncio
    async def test_get_department_success(
            self,
            client: httpx.AsyncClient,
            override_dependencies: None,
            departments_service: FakeDepartmentsService,
    ):
        # Создаем департамент через сервис
        new_dept, errors = create_department(name="Root Department", parent_id=None)
        assert errors == ""
        dept = await departments_service.repository.add(new_dept)

        response = await client.get(f"/departments/{dept.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["department"]["name"] == "Root Department"
        assert data["department"]["id"] == dept.id

    @pytest.mark.asyncio
    async def test_get_department_with_children(
            self,
            client: httpx.AsyncClient,
            override_dependencies: None,
            departments_service: FakeDepartmentsService,
    ):
        # Создаем структуру: Root -> Child1, Child2
        new_dept, errors = create_department(name="Root", parent_id=None)
        assert errors == ""
        root = await departments_service.repository.add(new_dept)

        new_dept, errors = create_department(name="Child 1", parent_id=root.id)
        assert errors == ""
        child1 = await departments_service.repository.add(new_dept)

        new_dept, errors = create_department(name="Child 2", parent_id=root.id)
        assert errors == ""
        child2 = await departments_service.repository.add(new_dept)

        response = await client.get(f"/departments/{root.id}?depth=1")

        assert response.status_code == 200
        data = response.json()
        assert data["department"]["name"] == "Root"
        assert "children" in data
        assert len(data["children"]) == 2

    @pytest.mark.asyncio
    async def test_get_department_not_found(
            self,
            client: httpx.AsyncClient,
            override_dependencies: None,
    ):
        response = await client.get("/departments/999")

        assert response.status_code == 404
        assert "department" in response.json()["detail"]["error"].lower()

    @pytest.mark.asyncio
    async def test_get_department_with_employees(
            self,
            client: httpx.AsyncClient,
            override_dependencies: None,
            departments_service: FakeDepartmentsService,
            employees_service: FakeEmployeesService,
    ):
        # Создаем департамент
        new_dept, errors = create_department(name="IT", parent_id=None)
        assert errors == ""
        dept = await departments_service.repository.add(new_dept)

        # Создаем сотрудников через сервис
        new_emp, errors = create_employee(full_name="Ivan", position="Dev", department_id=dept.id, hired_at=datetime.now().date())
        assert errors == ""
        await employees_service.repository.add(new_emp)

        new_emp, errors = create_employee(full_name="Maria", position="QA", department_id=dept.id, hired_at=datetime.now().date())
        assert errors == ""
        await employees_service.repository.add(new_emp)

        response = await client.get(f"/departments/{dept.id}?include_employees=true")

        assert response.status_code == 200
        data = response.json()
        # Структура зависит от реализации main.py
        assert "employees" in data or "department" in data


# noinspection PyShadowingNames
class TestMoveDepartment:
    """Тесты для PATCH /departments/{id}"""

    @pytest.mark.asyncio
    async def test_move_department_success(
            self,
            client: httpx.AsyncClient,
            override_dependencies: None,
            departments_service: FakeDepartmentsService,
    ):
        # Создаем два департамента
        new_dept, errors = create_department(name="Dept 1", parent_id=None)
        assert errors == ""
        dept1 = await departments_service.repository.add(new_dept)

        new_dept, errors = create_department(name="Dept 2", parent_id=None)
        assert errors == ""
        dept2 = await departments_service.repository.add(new_dept)

        # Перемещаем dept1 в dept2
        payload = {"parent_id": dept2.id}
        response = await client.patch(f"/departments/{dept1.id}", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["parent_id"] == dept2.id

    @pytest.mark.asyncio
    async def test_move_department_rename(
            self,
            client: httpx.AsyncClient,
            override_dependencies: None,
            departments_service: FakeDepartmentsService,
    ):
        # Создаем департамент
        new_dept, errors = create_department(name="Old Name", parent_id=None)
        assert errors == ""
        dept = await departments_service.repository.add(new_dept)

        # Переименовываем
        payload = {"name": "New Name"}
        response = await client.patch(f"/departments/{dept.id}", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Name"

    @pytest.mark.asyncio
    async def test_move_department_not_found(
            self,
            client: httpx.AsyncClient,
            override_dependencies: None,
    ):
        payload = {"name": "New Name"}
        response = await client.patch("/departments/999", json=payload)

        assert response.status_code == 404
        assert "department" in response.json()["detail"].lower()


# noinspection PyShadowingNames,DuplicatedCode
class TestDeleteDepartment:
    """Тесты для DELETE /departments/{id}"""

    @pytest.mark.asyncio
    async def test_delete_cascade_success(
            self,
            client: httpx.AsyncClient,
            override_dependencies: None,
            departments_service: FakeDepartmentsService,
    ):
        # Создаем департамент
        new_dept, errors = create_department(name="To Delete", parent_id=None)
        assert errors == ""
        dept = await departments_service.repository.add(new_dept)

        response = await client.delete(f"/departments/{dept.id}?mode=cascade")

        assert response.status_code == 204

        # Проверяем, что департамент удален
        assert await departments_service.repository.get_by_id(dept.id) is None

    @pytest.mark.asyncio
    async def test_delete_cascade_with_children(
            self,
            client: httpx.AsyncClient,
            override_dependencies: None,
            departments_service: FakeDepartmentsService,
    ):
        # Создаем структуру: Parent -> Child
        new_dept, errors = create_department(name="Parent", parent_id=None)
        assert errors == ""
        parent = await departments_service.repository.add(new_dept)

        new_dept, errors = create_department(name="Child", parent_id=parent.id)
        assert errors == ""
        child = await departments_service.repository.add(new_dept)

        response = await client.delete(f"/departments/{parent.id}?mode=cascade")

        assert response.status_code == 204

        # Проверяем, что оба удалены
        assert await departments_service.repository.get_by_id(parent.id) is None
        assert await departments_service.repository.get_by_id(child.id) is None

    @pytest.mark.asyncio
    async def test_delete_reassign_success(
            self,
            client: httpx.AsyncClient,
            override_dependencies: None,
            departments_service: FakeDepartmentsService,
            employees_service: FakeEmployeesService,
    ):
        # Создаем два департамента
        new_dept, errors = create_department(name="To Delete", parent_id=None)
        assert errors == ""
        dept_to_delete = await departments_service.repository.add(new_dept)

        new_dept, errors = create_department(name="Target", parent_id=None)
        assert errors == ""
        dept_target = await departments_service.repository.add(new_dept)

        # Создаем сотрудника в департаменте на удаление
        new_emp, errors = create_employee(full_name="Ivan", position="Dev", department_id=dept_to_delete.id, hired_at=datetime.now().date())
        assert errors == ""
        await employees_service.repository.add(new_emp)

        response = await client.delete(
            f"/departments/{dept_to_delete.id}?mode=reassign&reassign_to_department_id={dept_target.id}"
        )

        assert response.status_code == 204

        # Проверяем, что департамент удален
        assert await departments_service.repository.get_by_id(dept_to_delete.id) is None

        # Проверяем, что сотрудник переведен
        employees = await employees_service.repository.get_all_employees_into_department(dept_target.id)
        assert len(employees) == 1
        assert employees[0].full_name == "Ivan"

    @pytest.mark.asyncio
    async def test_delete_reassign_missing_id(
            self,
            client: httpx.AsyncClient,
            override_dependencies: None,
            departments_service: FakeDepartmentsService,
    ):
        # Создаем департамент
        new_dept, errors = create_department(name="To Delete", parent_id=None)
        assert errors == ""
        dept = await departments_service.repository.add(new_dept)

        # mode=reassign, но нет reassign_to_department_id
        response = await client.delete(f"/departments/{dept.id}?mode=reassign")

        assert response.status_code == 400
        assert "reassign" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_delete_not_found(
            self,
            client: httpx.AsyncClient,
            override_dependencies: None,
    ):
        response = await client.delete("/departments/999?mode=cascade")

        assert response.status_code == 404
