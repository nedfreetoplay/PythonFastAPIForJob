import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
    AsyncEngine
)

# Глобальные переменные для переиспользования
_engine: AsyncEngine | None = None
_async_session_maker: async_sessionmaker[AsyncSession] | None = None

def create_database_url(
        username: str,
        password: str,
        host: str,
        port: str,
        database: str,
) -> str:
    return f"postgresql+asyncpg://{username}:{password}@{host}:{port}/{database}"

def init_db(database_url: str) -> None:
    """
    Инициализация базы данных.

    Вызывается один раз при старте приложения.
    """
    global _engine, _async_session_maker

    _engine = create_async_engine(
        database_url,
        echo=False,  # Включить для отладки SQL
        pool_pre_ping=True,  # Проверять соединения перед использованием
        pool_size=10,  # Размер пула соединений
        max_overflow=20,  # Максимальное количество дополнительных соединений
    )

    _async_session_maker = async_sessionmaker(
        bind=_engine,
        class_=AsyncSession,
        expire_on_commit=False,  # Не истощать объекты после коммита
        autoflush=False,  # Отключить автоматический flush
    )


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency для FastAPI или другого ASGI фреймворка.

    Пример использования в FastAPI:
    ```python
    @app.get("/users")
    async def get_users(session: AsyncSession = Depends(get_session)):
        ...
    ```
    """
    if _async_session_maker is None:
        raise RuntimeError("Database not initialized. Call init_db() first")

    async with _async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def get_session_maker() -> async_sessionmaker[AsyncSession]:
    """
    Получить sessionmaker напрямую (для использования вне зависимостей).

    Пример:
    ```python
    async def some_function():
        async_session = get_session_maker()
        async with async_session() as session:
            ...
    ```
    """
    if _async_session_maker is None:
        raise RuntimeError("Database not initialized. Call init_db() first")
    return _async_session_maker


async def dispose_db() -> None:
    """Закрыть все соединения с базой данных"""
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan контекст для управления жизненным циклом приложения.

    Использование:
    ```python
    from src.data_access.session import lifespan
    app = FastAPI(lifespan=lifespan)
    ```
    """
    # Startup
    database_url = create_database_url(
        username=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        database=os.getenv("DB_NAME")
    )
    init_db(database_url)

    # FastAPI работает
    yield

    # Shutdown
    await dispose_db()
