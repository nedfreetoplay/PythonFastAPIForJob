from typing import Optional, List

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.abstractions.department_repo_protocol import DepartmentRepositoryProtocol
from src.core.models.department import ReadDepartment, CreateDepartment, UpdateDepartment
from src.data_access.entities.entities import Department


class DepartmentRepository(DepartmentRepositoryProtocol):
    """Репозиторий для работы с подразделениями"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, depart: CreateDepartment) -> ReadDepartment:
        new_department = Department(
            name = depart.name,
            parent_id = depart.parent_id,
        )

        self.session.add(new_department)
        await self.session.flush()  # Получаем ID без коммита
        await self.session.refresh(new_department)

        created_department = ReadDepartment(
            id = new_department.id,
            name = new_department.name,
            parent_id = new_department.parent_id,
            created_at = new_department.created_at,
        )

        return created_department

    async def get_by_id(self, department_id: int) -> Optional[ReadDepartment]:
        result = await self.session.execute(
            select(Department).where(Department.id == department_id)
        )
        depart = result.scalar_one_or_none()
        if not depart:
            return None

        read_department = ReadDepartment(
            id = depart.id,
            name = depart.name,
            parent_id = depart.parent_id,
            created_at = depart.created_at,
        )

        return read_department

    async def get_children(self, department_id: int) -> List[ReadDepartment]:
        result = await self.session.execute(
            select(Department).where(Department.parent_id == department_id)
        )
        children_raw = result.scalars()

        children: List[ReadDepartment] = []

        for child in children_raw:
            depart = ReadDepartment(
                id = child.id,
                name = child.name,
                parent_id = child.parent_id,
                created_at = child.created_at,
            )
            children.append(depart)

        return children

    async def is_exists(self, department_id: int) -> bool:
        result = await self.session.execute(
            select(Department).where(Department.id == department_id)
        )
        return result.scalar_one_or_none() is not None

    async def get_all_descendants_ids(self, department_id: int) -> set[int]:
        cte = (
            select(Department.id, Department.parent_id)
            .where(Department.id == department_id)
            .cte(name="department_tree", recursive=True)
        )

        recursive_part = select(Department.id, Department.parent_id).join(
            cte, Department.parent_id == cte.c.id
        )

        cte = cte.union_all(recursive_part)

        # Получаем все ID кроме корневого
        result = await self.session.execute(
            select(cte.c.id).where(cte.c.id != department_id)
        )
        return {row[0] for row in result.fetchall()}

    async def has_cycle(self, department_id: int | None, new_parent_id: int | None) -> bool:
        # Новое подразделение не может создать цикл
        if department_id is None:
            return False

        # Корневой департамент (без родителя) безопасен
        if new_parent_id is None:
            return False

        # Нельзя быть родителем самого себя
        if department_id == new_parent_id:
            return True

        # Получаем всех потомков текущего подразделения.
        descendants = await self.get_all_descendants_ids(department_id)

        # Если новый родитель среди потомков - будет цикл
        return new_parent_id in descendants


    async def update(self, department_id: int, depart: UpdateDepartment) -> ReadDepartment:
        d = await self.session.execute(
            select(Department).where(Department.id == department_id)
        )
        dept: Department | None = d.scalar_one_or_none()

        update_values = {}
        if depart.name is not None and dept.name != depart.name:
            update_values['name'] = depart.name
        if dept.parent_id != depart.parent_id:
            update_values['parent_id'] = depart.parent_id

        result = await self.session.execute(
            update(Department)
            .where(Department.id == department_id)
            .values(**update_values)
            .returning(Department)
        )
        return result.scalar_one_or_none()

    async def delete_with_cascade(self, department_id: int) -> bool:
        result = await self.session.execute(
            select(Department).where(Department.id == department_id)
        )
        depart = result.scalar_one_or_none()
        if not depart:
            return False

        # ORM автоматически удалит все связанные транзакции
        await self.session.delete(depart)
        return True

    async def delete_without_cascade(self, department_id: int) -> bool:
        result = await self.session.execute(
            delete(Department).where(Department.id == department_id)
        )
        return result.rowcount > 0

