from typing import Protocol, Optional

from src.core.models.employee import CreateEmployee, ReadEmployee


class EmployeeRepositoryProtocol(Protocol):

    async def add(self, employee: CreateEmployee) -> ReadEmployee:
        """
        Создание сотрудника и добавление его в подразделение
        :param employee: Новый сотрудник
        :return: Созданный сотрудник
        """
        ...

    async def get_by_id(self, employee_id: int) -> Optional[ReadEmployee]:
        """
        Поиск сотрудника по id.
        :param employee_id: ID сотрудника.
        :return: ReadEmployee или None
        """
        ...

    async def get_all_employees_into_department(self, department_id: int) -> list[ReadEmployee]:
        """
        Получить всех сотрудников относящиеся к определенному подразделению.
        :param department_id: ID подразделения.
        :return: Список сотрудников.
        """
        ...

    async def is_exists(self, employee_id: int) -> bool:
        """Проверка, существует ли такой сотрудник?"""
        ...

    async def delete(self, employee_id: int) -> bool:
        """
        Удаляет сотрудника по id.
        :param employee_id: ID сотрудника.
        :return: Удалось ли удалить?
        """
        ...