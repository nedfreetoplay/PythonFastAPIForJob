import datetime

from pydantic import BaseModel

NAME_MAX_LENGTH = 250

class CreateDepartment(BaseModel):
    name: str
    parent_id: int | None


class UpdateDepartment(BaseModel):
    name: str | None = None
    parent_id: int | None = None


class ReadDepartment(BaseModel):
    id: int
    name: str
    parent_id: int | None
    created_at: datetime.datetime


def create_department(
        name: str,
        parent_id: int | None = None,
):
    """
    Создание подразделения

    :param name: Название
    :param parent_id: ID родительского подразделения, если есть!
    :return: CreateDepartment и errors
    """

    errors = []

    if name is None or len(name) == 0:
        errors.append("Name is required")
    if len(name) > NAME_MAX_LENGTH:
        errors.append("Name cannot be longer than {}".format(NAME_MAX_LENGTH))

    errors_str = '\n'.join(errors)

    return CreateDepartment(
        name=name,
        parent_id=parent_id,
    ), errors_str

def create_update_department(
        name: str | None = None,
        parent_id: int | None = None,
):
    """
    Создание обновления для подразделения

    :param name: Название
    :param parent_id: ID родительского подразделения, если есть!
    :return: CreateDepartment и errors
    """

    errors = []
    if name is not None:
        if len(name) == 0:
            errors.append("Name не может быть пустым")
        if len(name) > NAME_MAX_LENGTH:
            errors.append("Name cannot be longer than {}".format(NAME_MAX_LENGTH))

    errors_str = '\n'.join(errors)

    return UpdateDepartment(
        name=name,
        parent_id=parent_id,
    ), errors_str