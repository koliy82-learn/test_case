# Используем официальный образ Python
FROM python:3.9-slim

# Устанавливаем рабочий каталог
WORKDIR /code

# Копируем зависимости и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем остальные файлы приложения
COPY . .

# Указываем команду по умолчанию для запуска
CMD ["flask", "run", "--host=0.0.0.0"]