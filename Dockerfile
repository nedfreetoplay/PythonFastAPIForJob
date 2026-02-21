FROM python:3.14-slim

WORKDIR /code

# Устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь код проекта
# main.py, src/, settings/ и т.д.
COPY . .

# Открываем порт
EXPOSE 8000

# Запускаем uvicorn напрямую, указывая на main.py в корне
# main:app означает: файл main.py, переменная app внутри него
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]