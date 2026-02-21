from typing import List, Annotated, Literal

import uvicorn
from fastapi import FastAPI, Depends, HTTPException, Query
from starlette import status

from src.api.contracts.create_department import CreateDepartment as apiCreateDepartment, ResponseCreateDepartment
from src.api.contracts.create_employee import CreateEmployee as apiCreateEmployee, ResponseCreateEmployee
from src.api.contracts.get_department import DepartmentGetResponse
from src.api.contracts.move_department import MoveDepartment as apiMoveDepartment, ResponseMoveDepartment
from src.core.abstractions.departments_service_protocol import DeleteMode, DepartmentsServiceProtocol
from src.core.abstractions.employees_service_protocol import EmployeesServiceProtocol
from src.core.models.department import CreateDepartment, UpdateDepartment, ReadDepartment
from src.core.models.employee import CreateEmployee, ReadEmployee
from src.data_access.session import lifespan
from src.dependencies import get_employees_service, get_departments_service

app = FastAPI(
    title="Department",
    description="API организационной структуры",
    version="1.0.0",
    lifespan=lifespan
)

@app.post(
    "/departments/{id}/employees",
    description="Создать сотрудника в подразделении"
)
async def create_employees_in_department(
    id: int,
    body: apiCreateEmployee,
    employees_service: EmployeesServiceProtocol = Depends(get_employees_service),
    depart_service: DepartmentsServiceProtocol = Depends(get_departments_service),
) -> ResponseCreateEmployee:
    """Создать сотрудника в подразделении"""
    try:
        # Проверяем, существует ли департамент
        if id is not None:
            dept = await depart_service.get_department(id)
            if not dept:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail={
                        "error": "department_not_found",
                        "message": f"Департамент с id={id} не найден",
                        "provided_id": id
                    }
                )

        # Если всё ок — создаём
        body = CreateEmployee(
            department_id=id,
            full_name=body.full_name,
            position=body.position,
            hired_at=body.hired_at,
        )

        result = await employees_service.create_employee(body)

        response = ResponseCreateEmployee(
            id=result.id,
            department_id=result.department_id,
            full_name=result.full_name,
            position=result.position,
            hired_at=result.hired_at,
            created_at=result.created_at,
        )

        return response
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@app.get(
    "/departments/{id}",
    description="Получить подразделение (детали + сотрудники + поддерево)"
)
async def get_department_by_id(
    id: int,
    include_employees: Annotated[bool, Query()] = True,
    depth: Annotated[int, Query()] = 0,
    depart_service: DepartmentsServiceProtocol = Depends(get_departments_service),
    employees_service: EmployeesServiceProtocol = Depends(get_employees_service),
):
    """Получить подразделение (детали + сотрудники + поддерево)"""
    try:
        if id is not None:
            dept = await depart_service.get_department(id)
            if not dept:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail={
                        "error": "department_not_found",
                        "message": f"Департамент с id={id} не найден",
                        "provided_id": id
                    }
                )

        if depth > 5:
            depth = 5
        if depth < 0:
            depth = 0

        all_children: List[ReadDepartment] = []
        all_employees: List[ReadEmployee] = []

        async def collect_children_recursively(department_id: int, current_depth: int = 0):
            """Рекурсивный сбор всех детей подразделения до заданной глубины"""
            if current_depth >= depth:
                return

            children = await depart_service.get_department_children(department_id)

            for c in children:
                all_children.append(c)
                # Рекурсивно собираем детей этого ребенка
                await collect_children_recursively(c.id, current_depth + 1)

        # Запускаем сбор с корневого подразделения
        await collect_children_recursively(id)

        # Если нужны сотрудники
        if include_employees:
            # Собираем всех сотрудников
            for child in all_children:
                employees = await employees_service.get_all_employees_into_department(child.id)
                all_employees.extend(employees)

            # Сортируем
            all_employees.sort(key=lambda x: x.created_at)

        # noinspection PyUnboundLocalVariable
        return DepartmentGetResponse(
            department=dept,
            children=all_children,
            employees=all_employees
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@app.patch(
    "/departments/{id}",
    description="Переместить подразделение в другое (изменить parent)"
)
async def department_move(
    id: int,
    body: apiMoveDepartment,
    depart_service: DepartmentsServiceProtocol = Depends(get_departments_service),
) -> ResponseMoveDepartment:
    """Переместить подразделение в другое (изменить parent)"""
    try:
        dept = await depart_service.get_department(id)
        if dept is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="department_not_found"
            )

        update_depart = UpdateDepartment(
            name=body.name,
            parent_id=body.parent_id
        )

        result = await depart_service.update_department(id, update_depart)

        response = ResponseMoveDepartment(
            id=result.id,
            name=result.name,
            parent_id=result.parent_id,
            created_at=result.created_at,
        )

        return response
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@app.delete(
    "/departments/{id}",
    description="Удалить подразделение"
)
async def department_remove(
    id: int,
    mode: Annotated[Literal["cascade", "reassign"], Query()] = "cascade", # Режим удаления подразделения
    reassign_to_department_id: Annotated[int | None, Query()] = None,     # ID подразделения для перевода сотрудников (обязательно при mode=reassign)
    depart_service: DepartmentsServiceProtocol = Depends(get_departments_service),
):
    """Удалить подразделение"""

    # Проверка query параметров
    if mode == "reassign" and reassign_to_department_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Поле reassign_to_department_id обязательно при mode="reassign"'
        )
    if mode == "cascade" and reassign_to_department_id is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Поле reassign_to_department_id должно быть пустым при mode="cascade"'
        )

    try:
        if mode == "cascade":
            delete_mode = DeleteMode.CASCADE
        elif mode == "reassign":
            delete_mode = DeleteMode.REASSIGN
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Поле mode почему-то не содержит cascade или reassign.'
            )

        errors = await depart_service.delete_department(
            department_id=id,
            mode=delete_mode,
            reassign_to_department_id=reassign_to_department_id
        )

        if errors:
            return HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=errors
            )
        else:
            return status.HTTP_204_NO_CONTENT
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@app.post(
    "/departments",
    description="Создать подразделение"
)
async def departments(
    body: apiCreateDepartment,
    depart_service: DepartmentsServiceProtocol = Depends(get_departments_service),
) -> ResponseCreateDepartment:
    """Создать подразделение"""
    try:
        # Проверяем, если такое подразделение, если нету, то depart_id=None
        depart_id: int | None = None
        if body.parent_id is not None:
            result = await depart_service.get_department(body.parent_id)
            if result is not None:
                depart_id = result.id

        create_depart = CreateDepartment(
            name=body.name,
            parent_id=depart_id,
        )

        result = await depart_service.create_department(create_depart)

        response = ResponseCreateDepartment(
            id=result.id,
            name=result.name,
            parent_id=result.parent_id,
            created_at=result.created_at,
        )

        return response
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@app.get(
    "/health",
    description="Проверка работоспособности"
)
async def health_check():
    """Проверка работоспособности"""
    return {"status": "ok"}


if __name__ == '__main__':
    # В Docker этот блок игнорируется, так как запускается через uvicorn CLI
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
