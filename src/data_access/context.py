from typing import Optional, Self, AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.abstractions.department_repo_protocol import DepartmentRepositoryProtocol
from src.core.abstractions.employee_repo_protocol import EmployeeRepositoryProtocol
from src.data_access.repositories.department_repository import DepartmentRepository
from src.data_access.repositories.employee_repository import EmployeeRepository
from src.data_access.session import get_session_maker


class DbContext:
    """
    Контекст базы данных.

    Управляет транзакциями и предоставляет доступ к репозиториям.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

        self._department_repo: Optional[DepartmentRepositoryProtocol] = None
        self._employee_repo: Optional[EmployeeRepositoryProtocol] = None
        self._committed = False

    @property
    def department(self) -> DepartmentRepositoryProtocol:
        if self._department_repo is None:
            self._department_repo = DepartmentRepository(self.session)
        return self._department_repo

    @property
    def employee(self) -> EmployeeRepositoryProtocol:
        if self._employee_repo is None:
            self._employee_repo = EmployeeRepository(self.session)
        return self._employee_repo

    async def commit(self) -> None:
        """Зафиксировать транзакцию"""
        await self.session.commit()
        self._committed = True

    async def rollback(self) -> None:
        """Откатить транзакцию"""
        await self.session.rollback()
        self._committed = False

    async def close(self) -> None:
        """Закрыть сессию"""
        await self.session.close()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type is not None:
            # При ошибке откатываем транзакцию
            await self.rollback()
        elif not self._committed:
            # Если не было коммита - коммитим автоматически
            await self.commit()
        await self.close()


async def get_db_context() -> AsyncGenerator[DbContext, None]:
    """
    Dependency для FastAPI.

    Пример использования:
    ```python
    @app.post("/users")
    async def create_user(db: DbContext = Depends(get_db_context)):
        user = await db.users.create(username="John", email="john@example.com")
        return user
    ```
    :return:
    """
    session_maker = get_session_maker()
    async with session_maker() as session:
        async with DbContext(session) as db:
            try:
                yield db
            except Exception:
                await db.rollback()
                raise
