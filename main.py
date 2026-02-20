import uvicorn
from fastapi import FastAPI

from src.data_access.session import lifespan, init_db, create_database_url
from src.config import Config

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
async def departments():
    """Создать подразделение"""
    pass

@app.post("/departments/{id}/employees")
async def create_employees_in_department(id: int):
    """Создать сотрудника в подразделении"""
    pass

@app.get("/departments/{id}")
async def get_department_by_id(id: int):
    """"Получить подразделение (детали + сотрудники + поддерево)"""
    pass

@app.patch("/departments/{id}")
async def department_move(id: int):
    """Переместить подразделение в другое (изменить parent)"""
    pass

@app.delete("/departments/{id}")
async def department_remove(id: int):
    """Удалить подразделение"""
    pass

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