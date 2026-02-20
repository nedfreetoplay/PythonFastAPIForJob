from typing import TypeVar, Generic, Optional, List

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

T = TypeVar('T', bound=DeclarativeBase)


class BaseRepository(Generic[T]):
    """Базовый репозиторий с общими CRUD операциями"""

    def __init__(self, session: AsyncSession, model: type[T]):
        self.session = session
        self.model = model

    async def get_by_id(self, id: int) -> Optional[T]:
        result = await self.session.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()

    async def get_all(self) -> List[T]:
        result = await self.session.execute(select(self.model))
        return list(result.scalars().all())

    async def filter_by(self, **kwargs) -> List[T]:
        """
        #TODO: Нужно прояснить как он работает
        :param kwargs:
        :return:
        """
        query = select(self.model)
        for key, value in kwargs.items():
            query = query.where(getattr(self.model, key) == value)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create(self, **kwargs) -> T:
        """
        #TODO: Прояснить зачем нужны kwargs
        :param kwargs:
        :return:
        """
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.flush() # Получаем ID без коммита
        await self.session.refresh(instance)
        return instance

    async def update(self, id: int, **kwargs) -> Optional[T]:
        stmt = (
            update(self.model)
            .where(self.model.id == id)
            .values(**kwargs)
            .returning(self.model)
        )
        result = await self.session.execute(stmt)
        instance = result.scalar_one_or_none()
        if instance:
            await self.session.refresh(instance)
        return instance

    async def delete(self, id: int) -> bool:
        stmt = delete(self.model).where(self.model.id == id)
        result = await self.session.execute(stmt)
        return result.rowcount > 0 #TODO: Возможно не работает

    async def exists(self, **kwargs) -> bool:
        """
        #TODO: Прояснить что делает функция и kwargs
        :param kwargs:
        :return:
        """
        query = select(self.model.id)
        for key, value in kwargs.items():
            query = query.where(getattr(self.model, key) == value)
        result = await self.session.execute(query.limit(1))
        return result.scalar_one_or_none() is not None