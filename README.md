# Freelance Marketplace API

Backend API платформа для работы между клиентами и фрилансерами, аналогичная Upwork.

Проект реализован на Django Rest Framework и предоставляет REST API для управления пользователями, проектами, предложениями, контрактами, отзывами и чатом.

## Возможности системы

- клиенты публикуют проекты
- фрилансеры просматривают проекты и отправляют bids
- клиенты выбирают исполнителя
- при выборе bid создаётся контракт
- клиент завершает контракт
- после завершения можно оставить отзыв
- между клиентом и фрилансером создаётся чат по контракту

## Технологии

- Python
- Django
- Django Rest Framework
- PostgreSQL
- JWT Authentication
- django-filter
- drf-spectacular

## Роли пользователей

### Client

- создаёт проекты
- видит bids на свои проекты
- выбирает bid
- завершает контракт
- оставляет отзыв

### Freelancer

- смотрит открытые проекты
- отправляет bid
- видит свои контракты
- участвует в чате по контракту

## Основные сущности

- `User`
- `Project`
- `Bid`
- `Contract`
- `Review`
- `Conversation`
- `Message`

## Бизнес-логика

- только `client` может создавать project
- только `freelancer` может отправлять bid
- один freelancer может отправить только один bid на один project
- client может видеть bids только на свои проекты
- client может выбрать только один bid
- выбранный bid получает статус `accepted`
- остальные bids получают статус `rejected`
- после принятия bid создаётся `contract`
- client может завершить только свой активный contract
- review можно оставить только после завершения contract
- rating review должен быть от 1 до 5

## Аутентификация

Проект использует JWT authentication.

После логина пользователь получает:

- `access` token
- `refresh` token

Защищённые endpoints требуют заголовок:

```http
Authorization: Bearer <access_token>
```

## API Endpoints

### Authentication

| Method | Endpoint | Описание |
|---|---|---|
| POST | `/api/accounts/signup/` | Регистрация пользователя |
| POST | `/api/accounts/verify-signup-code/` | Подтверждение регистрации кодом |
| POST | `/api/accounts/login/` | Вход пользователя |
| POST | `/api/accounts/logout/` | Выход пользователя |
| GET | `/api/accounts/me/` | Профиль текущего пользователя |
| PATCH | `/api/accounts/me/` | Обновление профиля текущего пользователя |
| GET | `/api/accounts/freelancers/{id}/` | Публичный профиль фрилансера |
| POST | `/api/accounts/password/reset/request/` | Запрос на сброс пароля |
| POST | `/api/accounts/password/reset/confirm/` | Подтверждение сброса пароля |
| POST | `/api/accounts/password/change/` | Смена пароля |
| POST | `/api/token/` | Получение JWT токенов |
| POST | `/api/token/refresh/` | Обновление access token |
| POST | `/api/token/verify/` | Проверка токена |

### Projects

| Method | Endpoint | Описание |
|---|---|---|
| GET | `/api/projects/` | Список проектов |
| POST | `/api/projects/` | Создание проекта |
| GET | `/api/projects/{id}/` | Детали проекта |

Поддерживается:

- pagination
- search по `title`
- filter по `status`
- filter по `min_budget`
- filter по `max_budget`
- ordering по `created_at`, `budget`, `deadline`

### Bids

| Method | Endpoint | Описание |
|---|---|---|
| GET | `/api/bids/` | Список bids пользователя |
| POST | `/api/bids/` | Отправка bid |
| GET | `/api/bids/{id}/` | Детали bid |
| GET | `/api/bids/project/{project_id}/` | Bids по конкретному project для владельца |
| POST | `/api/bids/{id}/accept/` | Принятие bid клиентом |

### Contracts

| Method | Endpoint | Описание |
|---|---|---|
| GET | `/api/contracts/` | Список контрактов |
| GET | `/api/contracts/{id}/` | Детали контракта |
| POST | `/api/contracts/{id}/finish/` | Завершение контракта |

Контракт создаётся автоматически при принятии bid.

### Reviews

| Method | Endpoint | Описание |
|---|---|---|
| GET | `/api/reviews/` | Список отзывов |
| POST | `/api/reviews/` | Создание review |
| GET | `/api/reviews/{id}/` | Детали review |

### Chat

| Method | Endpoint | Описание |
|---|---|---|
| GET | `/api/chat/conversations/` | Список чатов пользователя |
| GET | `/api/chat/conversations/{id}/` | Детали чата |
| GET | `/api/chat/conversations/{id}/messages/` | Список сообщений |
| POST | `/api/chat/conversations/{id}/messages/` | Отправка сообщения |

## Примеры API сценариев

### Создание проекта

```http
POST /api/projects/
Authorization: Bearer <access_token>
Content-Type: application/json
```

```json
{
  "title": "Build DRF backend",
  "description": "Need a Django REST API for freelance marketplace with auth and contracts.",
  "budget": "1500.00",
  "deadline": "2026-03-30",
  "skills_required": "django, drf, postgresql"
}
```

### Отправка bid

```http
POST /api/bids/
Authorization: Bearer <access_token>
Content-Type: application/json
```

```json
{
  "project_id": 1,
  "proposal": "I can deliver this project within 7 days with full API documentation.",
  "price": "1200.00",
  "delivery_time_days": 7
}
```

### Создание review

```http
POST /api/reviews/
Authorization: Bearer <access_token>
Content-Type: application/json
```

```json
{
  "contract_id": 2,
  "rating": 5,
  "comment": "Great work, delivered on time and communication was clear."
}
```

## Installation

### 1. Клонировать репозиторий

```bash
git clone https://github.com/v207vv-max/min-upwork.git
cd min-upwork
```

### 2. Создать виртуальное окружение

```bash
python -m venv venv
```

### 3. Активировать виртуальное окружение

Windows:

```bash
venv\Scripts\activate
```

Linux / macOS:

```bash
source venv/bin/activate
```

### 4. Установить зависимости

```bash
pip install -r requirements.txt
```

### 5. Создать `.env`

Пример:

```env
SECRET_KEY=django-insecure-local-dev-key
DEBUG=True

DB_NAME=min_upwork
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432

EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=dev@example.com
EMAIL_HOST_PASSWORD=dev-password
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=dev@example.com
```

### 6. Применить миграции

```bash
python manage.py migrate
```

### 7. Создать суперпользователя

```bash
python manage.py createsuperuser
```

### 8. Запустить сервер

```bash
python manage.py runserver
```

## API Documentation

Swagger UI:

```text
/api/docs/
```

OpenAPI schema:

```text
/api/schema/
```

## Документация Postman

Коллекция Postman доступна в репозитории:

```text
postman/8-imtihon.postman_collection.json
```

## Фильтрация и поиск

### Projects

Примеры:

```text
/api/projects/?search=django
/api/projects/?min_budget=500&max_budget=2000
/api/projects/?status=open
/api/projects/?ordering=-budget
```

### Bids

```text
/api/bids/?status=pending
/api/bids/?project=1
```

### Contracts

```text
/api/contracts/?status=active
```

### Reviews

```text
/api/reviews/?rating=5
```

## Test users

Для локальной проверки можно использовать:

- `client1 / test33333+`
- `freelancer1 / test33333+`

Если эти пользователи ещё не созданы в базе, создай их вручную через API или через Django shell.

## Структура проекта

```text
accounts/
    models.py
    serializers.py
    services.py
    urls.py
    views.py

projects/
    models.py
    serializers.py
    filters.py
    services.py
    urls.py
    views.py

bids/
    models.py
    serializers.py
    filters.py
    services.py
    urls.py
    views.py

contracts/
    models.py
    serializers.py
    filters.py
    services.py
    urls.py
    views.py

reviews/
    models.py
    serializers.py
    filters.py
    services.py
    urls.py
    views.py

chat/
    models.py
    serializers.py
    services.py
    urls.py
    views.py

core/
    pagination.py
    permissions.py

config/
    settings.py
    urls.py
```

## Используемые библиотеки

- `Django`
- `djangorestframework`
- `djangorestframework-simplejwt`
- `django-filter`
- `drf-spectacular`
- `psycopg2-binary`
- `python-decouple`
- `Pillow`

## Примечания

- Все основные endpoints работают через DRF.
- Все ответы API возвращаются в JSON.
- Валидация входных данных выполняется через serializers.
- Swagger доступен для быстрого тестирования API.
