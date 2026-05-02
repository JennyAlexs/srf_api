# Srf Booking API

API для бронирования научного оборудования (ЦКП — Центр коллективного пользования).

## О проекте

Сервис позволяет:
- Управлять локациями и оборудованием (CRUD)
- Регистрироваться и входить в систему (JWT-аутентификация)
- Бронировать оборудование с проверкой доступности
- Получать аналитику загрузки оборудования
- Защищён от brute-force (rate limiting)

## Технологии

- **FastAPI** — веб-фреймворк
- **SQLAlchemy** + **aiosqlite** — асинхронная работа с БД
- **JWT** — аутентификация и авторизация
- **Pydantic** — валидация данных
- **SlowAPI** — ограничение частоты запросов
- **Pytest** — тестирование

## Установка и запуск

```bash
# Клонировать репозиторий
git clone <url>
cd srf_api

# Создать виртуальное окружение
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Установить зависимости
pip install -r requirements.txt

# Запустить сервер
uvicorn main:app --reload

Сервер запустится на http://127.0.0.1:8000

Документация API
Swagger UI: http://127.0.0.1:8000/docs

ReDoc: http://127.0.0.1:8000/redoc

Эндпоинты
Метод	Путь	Описание
POST	/auth/login	Вход в систему
POST	/users/	Регистрация
GET	/users/	Список пользователей
POST	/locations/	Создать локацию
GET	/locations/	Список локаций
POST	/facilities/	Создать оборудование
GET	/facilities/	Список оборудования
POST	/bookings/	Забронировать (требуется авторизация)
GET	/bookings/	Список бронирований
DELETE	/bookings/{id}	Удалить бронь
POST	/news/	Создать новость
GET	/news/	Список новостей
GET	/analytics/facility-usage	Аналитика загрузки оборудования
Тестирование
bash
pytest tests/test_auth.py -v
Автор
Алексеева Евгения Сергеевна, 2026