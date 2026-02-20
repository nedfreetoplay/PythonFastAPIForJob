from typing import Optional, List

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.abstractions.department_repo_protocol import DepartmentRepositoryProtocol
from src.core.models import department
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

    async def update(self, depart: UpdateDepartment) -> ReadDepartment:
        update_values = {}
        if depart.need_update_name and depart.name is not None:
            update_values['name'] = depart.name
        if depart.need_update_parent_id:
            update_values['parent_id'] = depart.parent_id

        result = await self.session.execute(
            update(Department)
            .where(Department.id == depart.department_id)
            .values(**update_values)
            .returning(Department)
        )
        return result.scalar_one_or_none()

    async def delete_with_cascade(self, department_id: int) -> bool:
        depart = await self.get_by_id(department_id)
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

