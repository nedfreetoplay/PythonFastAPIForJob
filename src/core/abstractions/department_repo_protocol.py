from typing import Protocol, Optional, List

from src.core.models.department import CreateDepartment, ReadDepartment, UpdateDepartment


class DepartmentRepositoryProtocol(Protocol):

    async def add(self, department: CreateDepartment) -> ReadDepartment:
        """Создание подразделения."""
        ...

    async def get_by_id(self, department_id: int) -> Optional[ReadDepartment]:
        """Поиск подразделения по id."""
        ...

    async def get_children(self, department_id: int) -> List[ReadDepartment]:
        """Поиск дочерних подразделений"""
        ...

    async def is_exists(self, department_id: int) -> bool:
        """Проверка, существует ли такое подразделение?"""
        ...

    async def update(self, depart: UpdateDepartment) -> ReadDepartment:
        """Обновляет поля у указанного подразделения."""
        ...

    async def delete_with_cascade(self, department_id: int) -> bool:
        """
        Полное удаление подразделения и всех дочерних подразделений со всеми сотрудниками (каскадное).

        Работает через ORM="all, delete-orphan".

        :param department_id: ID подразделения.
        :return: Удалось ли удалить?
        """
        ...

    async def delete_without_cascade(self, department_id: int) -> bool:
        """Удаление подразделения без каскада - сотрудники остаются с department_id = NULL."""
        ...