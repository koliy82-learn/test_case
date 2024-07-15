# Используем официальный образ Python
FROM python:3.9

# Устанавливаем рабочий каталог
WORKDIR /code

#pip
RUN python -m pip install --upgrade pip

# Копируем зависимости и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем остальные файлы приложения
COPY . .

# Указываем команду по умолчанию для запуска
CMD ["flask", "run", "--host=0.0.0.0"]