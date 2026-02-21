import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from starlette.testclient import TestClient

from main import app
from src.dependencies import get_employees_service, get_departments_service

# Добавляем корень проекта в sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Инициализация тестового клиента
client = TestClient(app)


# --- Фикстуры для моков ---

@pytest.fixture
def mock_depart_service():
    """Создает мок сервиса департаментов"""
    service = AsyncMock()
    # Дефолтное поведение, чтобы тесты не падали, если метод не настроен явно
    service.get_department = AsyncMock(return_value=None)
    service.create_department = AsyncMock(return_value=None)
    service.update_department = AsyncMock(return_value=None)
    service.delete_department = AsyncMock(return_value=[])
    service.get_department_children = AsyncMock(return_value=[])
    return service


@pytest.fixture
def mock_employees_service():
    """Создает мок сервиса сотрудников"""
    service = AsyncMock()
    service.create_employee = AsyncMock(return_value=None)
    service.get_all_employees_into_department = AsyncMock(return_value=[])
    return service


@pytest.fixture
def override_dependencies(mock_depart_service, mock_employees_service):
    """Переопределяет зависимости в приложении для использования моков"""
    async def override_depart():
        return mock_depart_service

    async def override_emp():
        return mock_employees_service

    app.dependency_overrides[get_departments_service] = override_depart
    app.dependency_overrides[get_employees_service] = override_emp

    yield

    # Очистка переопределений после теста
    app.dependency_overrides.clear()

# --- Тесты ---

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


class TestCreateDepartment:
    """Тесты для POST /departments"""

    def test_create_department_success_with_parent(self, override_dependencies, mock_depart_service):
        mock_parent = MagicMock(id=5)
        mock_new_dept = MagicMock(id=10, name="New Dept", parent_id=5, created_at="2023-01-01")

        mock_depart_service.get_department = AsyncMock(return_value=mock_parent)
        mock_depart_service.create_department = AsyncMock(return_value=mock_new_dept)

        payload = {"name": "New Dept", "parent_id": 5}
        response = client.post("/departments", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Dept"
        assert data["parent_id"] == 5

    def test_create_department_root(self, override_dependencies, mock_depart_service):
        # Parent не указан или не найден -> создается корневой
        mock_depart_service.get_department = AsyncMock(return_value=None) # Parent не найден
        mock_new_dept = MagicMock(id=10, name="Root Dept", parent_id=None, created_at="2023-01-01")
        mock_depart_service.create_department = AsyncMock(return_value=mock_new_dept)

        payload = {"name": "Root Dept", "parent_id": 999} # 999 не существует
        response = client.post("/departments", json=payload)

        assert response.status_code == 200
        # Согласно логике main.py, если parent не найден, depart_id станет None
        data = response.json()
        assert data["parent_id"] is None

    def test_create_department_validation_error(self, override_dependencies, mock_depart_service):
        mock_depart_service.get_department = AsyncMock(return_value=MagicMock(id=1))
        mock_depart_service.create_department = AsyncMock(side_effect=ValueError("Name too short"))

        payload = {"name": "A", "parent_id": 1}
        response = client.post("/departments", json=payload)

        assert response.status_code == 400


class TestCreateEmployeeInDepartment:
    """Тесты для POST /departments/{id}/employees"""

    def test_create_employee_success(self, override_dependencies, mock_depart_service, mock_employees_service):
        # Настройка моков
        mock_dept = MagicMock(id=1, name="IT")
        mock_depart_service.get_department = AsyncMock(return_value=mock_dept)

        mock_emp_result = MagicMock(
            id=101, department_id=1, full_name="Ivan", position="Dev",
            hired_at="2023-01-01", created_at="2023-01-01T10:00:00"
        )
        mock_employees_service.create_employee = AsyncMock(return_value=mock_emp_result)

        payload = {"full_name": "Ivan", "position": "Dev", "hired_at": "2023-01-01"}

        response = client.post("/departments/1/employees", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 101
        assert data["full_name"] == "Ivan"
        mock_depart_service.get_department.assert_called_once_with(1)
        mock_employees_service.create_employee.assert_called_once()

    def test_create_employee_dept_not_found(self, override_dependencies, mock_depart_service):
        # Департамент не найден
        mock_depart_service.get_department = AsyncMock(return_value=None)

        payload = {"full_name": "Ivan", "position": "Dev", "hired_at": "2023-01-01"}
        response = client.post("/departments/999/employees", json=payload)

        # В коде указан 422 для этой ошибки
        assert response.status_code == 422
        assert "department_not_found" in response.json()["detail"]["error"]

    def test_create_employee_validation_error(self, override_dependencies, mock_depart_service, mock_employees_service):
        # Мокируем успешное существование департамента
        mock_depart_service.get_department = AsyncMock(return_value=MagicMock(id=1))
        # Мокируем ошибку валидации в сервисе (ValueError)
        mock_employees_service.create_employee = AsyncMock(side_effect=ValueError("Invalid date"))

        payload = {"full_name": "Ivan", "position": "Dev", "hired_at": "invalid-date"}
        response = client.post("/departments/1/employees", json=payload)

        assert response.status_code == 400


class TestGetDepartment:
    """Тесты для GET /departments/{id}"""

    def test_get_department_success(self, override_dependencies, mock_depart_service, mock_employees_service):
        mock_dept = MagicMock(id=1, name="Root", parent_id=None, created_at="2023-01-01")
        mock_child = MagicMock(id=2, name="Child", parent_id=1, created_at="2023-01-01")

        mock_depart_service.get_department = AsyncMock(return_value=mock_dept)
        mock_depart_service.get_department_children = AsyncMock(return_value=[mock_child])
        mock_employees_service.get_all_employees_into_department = AsyncMock(return_value=[])

        response = client.get("/departments/1?include_employees=true&depth=1")

        assert response.status_code == 200
        data = response.json()
        assert data["department"]["name"] == "Root"
        assert len(data["children"]) == 1

    def test_get_department_not_found(self, override_dependencies, mock_depart_service):
        mock_depart_service.get_department = AsyncMock(return_value=None)

        response = client.get("/departments/999")

        assert response.status_code == 422
        assert "department_not_found" in response.json()["detail"]["error"]

    def test_get_department_depth_limit(self, override_dependencies, mock_depart_service, mock_employees_service):
        mock_depart_service.get_department = AsyncMock(return_value=MagicMock(id=1))
        mock_depart_service.get_department_children = AsyncMock(return_value=[])

        # depth > 5 должен обрезаться до 5 внутри логики, ошибок не должно быть
        response = client.get("/departments/1?depth=10")
        assert response.status_code == 200


class TestMoveDepartment:
    """Тесты для PATCH /departments/{id}"""

    def test_move_department_success(self, override_dependencies, mock_depart_service):
        mock_dept = MagicMock(id=1, name="Old Name", parent_id=None, created_at="2023-01-01")
        mock_updated = MagicMock(id=1, name="New Name", parent_id=2, created_at="2023-01-01")

        mock_depart_service.get_department = AsyncMock(return_value=mock_dept)
        mock_depart_service.update_department = AsyncMock(return_value=mock_updated)

        payload = {"name": "New Name", "parent_id": 2}
        response = client.patch("/departments/1", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Name"
        assert data["parent_id"] == 2

    def test_move_department_not_found(self, override_dependencies, mock_depart_service):
        mock_depart_service.get_department = AsyncMock(return_value=None)

        payload = {"name": "New Name", "parent_id": 2}
        response = client.patch("/departments/999", json=payload)

        # В коде PATCH указан 404 для not found
        assert response.status_code == 404
        assert response.json()["detail"] == "department_not_found"


class TestDeleteDepartment:
    """Тесты для DELETE /departments/{id}"""

    def test_delete_cascade_success(self, override_dependencies, mock_depart_service):
        mock_depart_service.delete_department = AsyncMock(return_value=[])  # Пустой список ошибок

        response = client.delete("/departments/1?mode=cascade")

        assert response.status_code == 204

    def test_delete_reassign_success(self, override_dependencies, mock_depart_service):
        mock_depart_service.delete_department = AsyncMock(return_value=[])

        response = client.delete("/departments/1?mode=reassign&reassign_to_department_id=5")

        assert response.status_code == 204

    def test_delete_reassign_missing_id(self, override_dependencies, mock_depart_service):
        # mode=reassign, но нет reassign_to_department_id
        response = client.delete("/departments/1?mode=reassign")

        assert response.status_code == 400
        assert "обязательно" in response.json()["detail"]

    def test_delete_cascade_with_reassign_id_error(self, override_dependencies, mock_depart_service):
        # mode=cascade, но передан reassign_to_department_id
        response = client.delete("/departments/1?mode=cascade&reassign_to_department_id=5")

        assert response.status_code == 400
        assert "должно быть пустым" in response.json()["detail"]

    def test_delete_service_errors(self, override_dependencies, mock_depart_service):
        mock_depart_service.delete_department = AsyncMock(return_value=["Error 1"])

        response = client.delete("/departments/1?mode=cascade")

        assert response.status_code == 400
