import datetime

from sqlalchemy import String, DateTime, ForeignKey, Date
from sqlalchemy.orm import Mapped, mapped_column

from src.database.base import Base
from src.utils import utc_now


class Department(Base):
    """
    Подразделение
    """
    __tablename__ = 'departments'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey('departments.id'))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=utc_now)


class Employee(Base):
    """
    Сотрудник
    """
    __tablename__ = 'employees'

    id: Mapped[int] = mapped_column(primary_key=True)
    department_id: Mapped[int | None] = mapped_column(ForeignKey('departments.id'))
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    position: Mapped[str] = mapped_column(String(200), nullable=False)
    hired_at: Mapped[datetime.date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=utc_now)