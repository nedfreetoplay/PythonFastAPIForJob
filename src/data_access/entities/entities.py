import datetime

from sqlalchemy import String, ForeignKey, DateTime, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.data_access.base import Base

def utc_now():
    datetime.datetime.now(datetime.UTC)

class Department(Base):
    """
    Подразделение
    """
    __tablename__ = 'departments'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey('departments.id', ondelete='SET NULL'),
        nullable=True
    )
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=utc_now)

    # Самосвязь
    children: Mapped[list[Department]] = relationship(
        "Department",
        back_populates="parent",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy='selectin',
    )

    parent: Mapped[Department] = relationship(
        "Department",
        back_populates="children",
        remote_side=[id],
        lazy="joined",
    )

    employees: Mapped[list[Employee]] = relationship(
        back_populates="department",
        cascade='all, delete-orphan',
        passive_deletes=True,
        lazy='selectin',
    )


class Employee(Base):
    """
    Сотрудник
    """
    __tablename__ = 'employees'

    id: Mapped[int] = mapped_column(primary_key=True)
    department_id: Mapped[int | None] = mapped_column(
        ForeignKey('departments.id', ondelete='SET NULL'),
        nullable=True,
    )
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    position: Mapped[str] = mapped_column(String(200), nullable=False)
    hired_at: Mapped[datetime.date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=utc_now)

    department: Mapped[Department] = relationship(back_populates='employees')