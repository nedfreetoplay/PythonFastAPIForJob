import datetime

from pydantic import BaseModel

FULLNAME_MAX_LENGTH = 250
POSITION_MAX_LENGTH = 250

class CreateEmployee(BaseModel):
    department_id: int
    full_name: str
    position: str
    hired_at: datetime.date | None


class ReadEmployee(BaseModel):
    id: int
    department_id: int
    full_name: str
    position: str
    hired_at: datetime.date | None
    created_at: datetime.datetime


def create_employee(
    department_id: int,
    full_name: str,
    position: str,
    hired_at: datetime.date,
):
    """
    Создание сотрудника

    :param department_id: ID депортамента к которому приписан сотрудник
    :param full_name: Полное имя сотрудника
    :param position: Позиция сотрудника
    :param hired_at: Дата найма сотрудника
    :return: CreateEmployee и errors
    """
    errors = []

    if full_name is None or len(full_name) > FULLNAME_MAX_LENGTH:
        errors.append("Full Name cannot be longer than {}".format(FULLNAME_MAX_LENGTH))

    if position is None or len(position) > POSITION_MAX_LENGTH:
        errors.append("Position cannot be longer than {}".format(POSITION_MAX_LENGTH))

    errors_str = '\n'.join(errors)

    return CreateEmployee(
        department_id=department_id,
        full_name=full_name,
        position=position,
        hired_at=hired_at,
    ), errors_str