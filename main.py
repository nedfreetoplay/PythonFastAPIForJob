import uvicorn
from fastapi import FastAPI

from src.database.session import init_db, lifespan

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

    uvicorn.run(
        "main:app",  # Импорт приложения из текущего модуля
        host="0.0.0.0",
        port=8000,
        reload=True,  # Автоматическая перезагрузка при разработке (Отключить в продакшене)
        workers=1,    # Количество воркеров = количество ядер CPU (Для разработки достаточно 1 воркера)
        log_level="info", # warning
        factory=False  # Не используем фабрику приложений
    )



if __name__ == '__main__':
    main()