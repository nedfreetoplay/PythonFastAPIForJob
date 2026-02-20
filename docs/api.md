# Какие должны быть реализованы API.

## Создать подразделение
Входящие параметры:

##### url:
- POST /departments/

##### body:
- name: str,
- parent_id: int | None

##### response:
- ReadDepartments

## Создать сотрудника в подразделение
##### url:
- POST /departments/{id}/employees/

##### body:
- full_name: str
- position: str
- hired_at: date | None

##### response:
- ReadEmployee

## Получить подразделение
##### url:
- GET /departments/{id}

##### body:
- depth: int
- include_employees: bool

##### response:
- department: ReadDepartments
- employees: List[ReadEmployee]
- children: List[ReadDepartments]

## Переместить подразделение в другое (изменить parent)
##### url:
- PATCH /departments/{id}

##### body:
- name: str,
- parent_id: int | None

##### response:
- ReadDepartments

## Удалить подразделение
##### url:
DELETE /departments/{id}

##### body:
- mode: str
- reassign_to_department_id: int

##### response:
- 204 No Content


# Сервисы и репозитории

Репозиторий максимально прост, ну там get, update, delete...

А вот сервисы уже должны принимать в себя те же параметры что и в api и проверять что всё допустимо
и взаимодействовать с репозиториями.

Стратегия каскадного удаления.

1. Сохраняем id подразделения который собираемся удалить в current.
2. Удаляем всех сотрудников связанных с этим подразделением.
3. Ищем подразделение у которого parent_id == current_id и сохраняем его в future.
4. Удаляем подразделение current.
5. current = future.
6. Вернутся к шагу 1.