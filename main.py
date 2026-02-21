from typing import List

import uvicorn
from fastapi import FastAPI, Depends, HTTPException
from starlette import status

from src.api.contracts.create_department import CreateDepartment as apiCreateDepartment, ResponseCreateDepartment
from src.api.contracts.create_employee import CreateEmployee as apiCreateEmployee, ResponseCreateEmployee
from src.api.contracts.delete_department import DepartmentDeleteRequest
from src.api.contracts.get_department import DepartmentGetRequest, DepartmentGetResponse
from src.api.contracts.move_department import MoveDepartment as apiMoveDepartment, ResponseMoveDepartment
from src.application.services.departments_service import DepartmentsService
from src.application.services.employees_service import EmployeesService
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

@app.get(
    "/health",
    description="Проверка работоспособности"
)
async def health_check():
    """Проверка работоспособности"""
    return {"status": "ok"}

@app.post(
    "/departments",
    description="Создать подразделение"
)
async def departments(
    new_depart: apiCreateDepartment,
    depart_service: DepartmentsServiceProtocol = Depends(get_departments_service),
) -> ResponseCreateDepartment:
    """Создать подразделение"""
    create_depart = CreateDepartment(
        name=new_depart.name,
        parent_id=new_depart.parent_id,
    )

    try:
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

@app.post(
    "/departments/{id}/employees",
    description="Создать сотрудника в подразделении"
)
async def create_employees_in_department(
    id: int,
    create_employee: apiCreateEmployee,
    employees_service: EmployeesServiceProtocol = Depends(get_employees_service),
) -> ResponseCreateEmployee:
    """Создать сотрудника в подразделении"""
    create_employee = CreateEmployee(
        department_id=id,
        full_name=create_employee.full_name,
        position=create_employee.position,
        hired_at=create_employee.hired_at,
    )
    try:
        result = await employees_service.create_employee(create_employee)

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
    query: DepartmentGetRequest,
    depart_service: DepartmentsServiceProtocol = Depends(get_departments_service),
    employees_service: EmployeesServiceProtocol = Depends(get_employees_service),
):
    """Получить подразделение (детали + сотрудники + поддерево)"""
    try:
        current_department = await depart_service.get_department(id)

        all_children: List[ReadDepartment] = []
        all_employees: List[ReadEmployee] = []

        async def collect_children_recursively(department_id: int, current_depth: int = 0):
            """Рекурсивный сбор всех детей подразделения до заданной глубины"""
            if current_depth >= query.depth:
                return

            children = await depart_service.get_department_children(department_id)

            for child in children:
                all_children.append(child)
                # Рекурсивно собираем детей этого ребенка
                await collect_children_recursively(child.id, current_depth + 1)

        # Запускаем сбор с корневого подразделения
        await collect_children_recursively(id)

        # Если нужны сотрудники
        if query.include_employees:
            # Собираем всех сотрудников
            for child in all_children:
                employees = await employees_service.get_all_employees_into_department(child.id)
                all_employees.extend(employees)

            # Сортируем
            all_employees.sort(key=lambda x: x.created_at)


        return DepartmentGetResponse(
            department=current_department,
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
    move_department: apiMoveDepartment,
    depart_service: DepartmentsServiceProtocol = Depends(get_departments_service),
) -> ResponseMoveDepartment:
    """Переместить подразделение в другое (изменить parent)"""
    update_depart = UpdateDepartment(
        department_id=id,
        name=move_department.name,
        parent_id=move_department.parent_id,
    )

    try:
        result = await depart_service.update_department(update_depart)

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
    query: DepartmentDeleteRequest,
    depart_service: DepartmentsServiceProtocol = Depends(get_departments_service),
):
    """Удалить подразделение"""
    mode = query.mode

    try:
        if mode == "cascade":
            result = await depart_service.delete_department(
                department_id=id,
                mode=DeleteMode.CASCADE,
                reassign_to_department_id=query.reassign_to_department_id
            )
        elif mode == "reassign":
            result = await depart_service.delete_department(
                department_id=id,
                mode=DeleteMode.REASSIGN,
                reassign_to_department_id=query.reassign_to_department_id
            )
        else:
            return status.HTTP_400_BAD_REQUEST

        if result is not None and len(result) > 0:
            return HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result
            )
        else:
            return status.HTTP_204_NO_CONTENT
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

if __name__ == '__main__':
    # В Docker этот блок игнорируется, так как запускается через uvicorn CLI
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
