import uvicorn
from fastapi import FastAPI, Depends, HTTPException
from starlette import status

from src.api.contracts.create_department import CreateDepartment as apiCreateDepartment, ResponseCreateDepartment
from src.api.contracts.create_employee import CreateEmployee as apiCreateEmployee, ResponseCreateEmployee
from src.api.contracts.delete_department import DepartmentDeleteRequest
from src.api.contracts.move_department import MoveDepartment as apiMoveDepartment, ResponseMoveDepartment
from src.application.services.departments_service import DepartmentsService, DeleteMode
from src.application.services.employees_service import EmployeesService
from src.config import Config
from src.core.models.department import CreateDepartment, UpdateDepartment
from src.core.models.employee import CreateEmployee
from src.data_access.session import lifespan, init_db, create_database_url

app = FastAPI(
    title="Department",
    description="API организационной структуры",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/health")
async def health_check():
    """Проверка работоспособности"""
    return {"status": "ok"}

@app.post("/departments")
async def departments(
    new_depart: apiCreateDepartment,
    depart_service: DepartmentsService = Depends(DepartmentsService),
) -> ResponseCreateDepartment:
    """Создать подразделение"""
    create_depart = CreateDepartment(
        name=new_depart.name,
        parent_id=new_depart.parent_id,
    )

    result = await depart_service.create_department(create_depart)

    response = ResponseCreateDepartment(
        id=result.id,
        name=result.name,
        parent_id=result.parent_id,
        created_at=result.created_at,
    )

    return response

@app.post("/departments/{id}/employees")
async def create_employees_in_department(
    id: int,
    create_employee: apiCreateEmployee,
    employees_service: EmployeesService = Depends(EmployeesService),
) -> ResponseCreateEmployee:
    """Создать сотрудника в подразделении"""
    create_employee = CreateEmployee(
        department_id=id,
        full_name=create_employee.full_name,
        position=create_employee.position,
        hired_at=create_employee.hired_at,
    )

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

@app.get("/departments/{id}")
async def get_department_by_id(
    id: int,
    query:
):
    """"Получить подразделение (детали + сотрудники + поддерево)"""
    pass

@app.patch("/departments/{id}")
async def department_move(
    id: int,
    move_department: apiMoveDepartment,
    depart_service: DepartmentsService = Depends(DepartmentsService),
) -> ResponseMoveDepartment:
    """Переместить подразделение в другое (изменить parent)"""
    update_depart = UpdateDepartment(
        department_id=id,
        name=move_department.name,
        parent_id=move_department.parent_id,
    )

    result = await depart_service.update_department(update_depart)

    response = ResponseMoveDepartment(
        id=result.id,
        name=result.name,
        parent_id=result.parent_id,
        created_at=result.created_at,
    )

    return response

@app.delete("/departments/{id}")
async def department_remove(
    id: int,
    query: DepartmentDeleteRequest,
    depart_service: DepartmentsService = Depends(DepartmentsService),
):
    """Удалить подразделение"""
    mode = query.mode
    result: str | None = None

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


def main():
    """Точка входа для запуска приложения"""
    print("Приложение запускается...")

    config = Config.load()
    fastapi_host = config.fastapi.host
    fastapi_port = config.fastapi.port
    env_user = config.db.host
    env_pass_secret = config.db.password.get_secret_value()

    if True:
        print(f"{config}")
        print(f"Secret password= {config.db.password.get_secret_value()}")

    print("Инициализация базы данных...")
    database_url = create_database_url(
        username=env_user,
        password=env_pass_secret,
        host=fastapi_host,
    )
    init_db("postgresql+asyncpg://user:password@localhost/dbname")

    print("Старт uvicorn сервера...")

    uvicorn.run(
        "main:app",  # Импорт приложения из текущего модуля
        host=fastapi_host,
        port=fastapi_port,
        reload=True,  # Автоматическая перезагрузка при разработке (Отключить в продакшене)
        workers=1,    # Количество воркеров = количество ядер CPU (Для разработки достаточно 1 воркера)
        log_level="info", # warning
        factory=False  # Не используем фабрику приложений
    )


if __name__ == '__main__':
    main()


# Пример
#from fastapi import FastAPI, Depends, HTTPException, status
# from contextlib import asynccontextmanager
# from database.session import init_db, dispose_db
# from database.context import get_db_context, DbContext
# from services.user_service import UserService
# from config import settings

# @app.post("/users", status_code=status.HTTP_201_CREATED)
# async def create_user(
#     username: str,
#     email: str,
#     db: DbContext = Depends(get_db_context)
# ):
#     service = UserService(db)
#     try:
#         user = await service.register_user(username, email)
#         return {
#             "id": user.id,
#             "username": user.username,
#             "email": user.email,
#             "balance": str(user.balance)
#         }
#     except ValueError as e:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=str(e)
#         )
#
#
# @app.post("/users/{user_id}/deposit")
# async def deposit(
#     user_id: int,
#     amount: str,
#     db: DbContext = Depends(get_db_context)
# ):
#     service = UserService(db)
#     try:
#         user = await service.deposit(user_id, amount)
#         return {
#             "id": user.id,
#             "username": user.username,
#             "new_balance": str(user.balance)
#         }
#     except ValueError as e:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=str(e)
#         )
#
#
# @app.get("/users/{user_id}")
# async def get_user(user_id: int, db: DbContext = Depends(get_db_context)):
#     service = UserService(db)
#     profile = await service.get_user_profile(user_id)
#     if not profile:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Пользователь не найден"
#         )
#     return profile
#
#
# @app.get("/health")
# async def health():
#     return {"status": "ok"}