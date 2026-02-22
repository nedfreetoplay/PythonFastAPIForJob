# Сборка и запуск
```
docker-compose up --build
```
Или
```
docker compose up --build
```

# Просмотр логов (если что-то не работает)

```
docker-compose logs -f api
```
Или
```
docker compose logs -f api
```

# Остановка
```
docker-compose down
```
Или
```
docker compose down
```

# Alembic (Миграции)

Создать миграцию:
```
alembic revision --autogenerate -m "My migration"
```

Применить миграцию:
```
alembic upgrade head
```

# Тестирование

Запустить автотесты
```
pytest
```