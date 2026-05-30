# microservices lab

## Structure:
```bash
# ├── docker-compose.yml      # Оркестрация всех сервисов: связи, сети, тома, переменные окружения
# ├── .env                    # Переменные окружения (пароли БД, секреты, порты)

# ├── gateway/                # API Gateway - единая точка входа
# │   ├── Dockerfile          # Сборка Nginx с модулем Lua или OpenResty
# │   └── nginx.conf          # Маршрутизация запросов:
# │                           #   /api/auth/*  → auth-service:5001
# │                           #   /api/users/* → users-service:5002
# │                           #   /api/orders/* → orders-service:5003
# │                           #   + rate limiting, CORS, JWT проверка (опционально)

# ├── services/
# │   ├── auth/               # Сервис аутентификации
# │   │   ├── Dockerfile      # Python 3.11-slim + установка зависимостей
# │   │   ├── app.py          # Эндпоинты:
# │   │   │                   #   POST /register - создание пользователя
# │   │   │                   #   POST /login - выдача JWT токена
# │   │   │                   #   POST /verify - проверка токена
# │   │   └── requirements.txt # Flask/JWT/cryptography/psycopg2-binary/redis

# │   ├── users/              # Сервис управления пользователями
# │   │   ├── Dockerfile      # Python 3.11-slim
# │   │   ├── app.py          # CRUD операции (требуют JWT):
# │   │   │                   #   GET    /users/:id - получить профиль
# │   │   │                   #   PUT    /users/:id - обновить данные
# │   │   │                   #   DELETE /users/:id - удалить аккаунт
# │   │   │                   #   GET    /users - список (админ)
# │   │   └── requirements.txt # Flask/JWT/psycopg2-binary

# │   └── orders/             # Сервис заказов
# │       ├── Dockerfile      # Python 3.11-slim
# │       ├── app.py          # Бизнес-логика заказов:
# │       │                   #   POST   /orders - создать заказ
# │       │                   #   GET    /orders/:id - получить заказ
# │       │                   #   GET    /orders/user/:user_id - заказы пользователя
# │       │                   #   PUT    /orders/:id/status - обновить статус
# │       │                   #   DELETE /orders/:id - отменить заказ
# │       └── requirements.txt # Flask/psycopg2-binary/redis (для кэша)

# └── infrastructure/
#     ├── postgres/           # Общая БД (для простоты, хотя в проде лучше разделять)
#     │   └── init.sql        # Инициализация БД:
#     │                       #   CREATE DATABASE auth_db, users_db, orders_db;
#     │                       #   CREATE TABLES: users, orders, refresh_tokens
#     └── redis/              # Кэш и сессии
#         └── (пусто)         # Используем стандартный образ redis:7-alpine
#                             # Задачи:
#                             #   - хранение черных списков JWT
#                             #   - кэширование профилей пользователей
#                             #   - rate limiting счетчики
#                             #   - временные данные (подтверждение email)
```

## Status codes:
| Code | Name | When to use |
|------|------|----------------|
| 200 | OK | Successful GET, PUT, DELETE |
| 201 | Created | Successful POST (resource created) |
| 204 | No Content | Successful DELETE (no response body) |
| 400 | Bad Request | Data validation error (invalid JSON, data type) |
| 401 | Unauthorized | No token or token is invalid |
| 403 | Forbidden | Token exists but insufficient rights (not own resource) |
| 404 | Not Found | Resource not found |
| 409 | Conflict | User/email already exists |
| 429 | Too Many Requests | Login attempt limit exceeded |
| 500 | Internal Server Error | Unexpected server error |
| 503 | Service Unavailable | Dependent service is unavailable |
