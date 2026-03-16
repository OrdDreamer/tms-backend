# TMS Backend

Django REST API для централізованого управління перекладами в проєктах.

![Version](https://img.shields.io/badge/version-0.1.0-blue)
![Python 3.12](https://img.shields.io/badge/python-3.12-blue)
![Django 6.0](https://img.shields.io/badge/django-6.0-green)
![DRF 3.16](https://img.shields.io/badge/DRF-3.16-red)
![License: MIT](https://img.shields.io/badge/license-MIT-green)

[English version README](README.md)

## Roadmap

Дивіться [docs/ROADMAP.md](docs/ROADMAP.md) для ознайомлення з планованими фічами та їх пріоритетами.

## Стек технологій

| Компонент     | Технологія                          |
| ------------- | ----------------------------------- |
| Фреймворк     | Django 6.0 + Django REST Framework  |
| База даних    | PostgreSQL 17                       |
| Кеш           | Redis 7                             |
| Автентифікація| JWT (simplejwt) з blacklist токенів |
| API документація | drf-spectacular (Swagger / ReDoc)|
| Контейнеризація | Docker + Docker Compose           |
| CI/CD         | GitHub Actions                      |
| Лінтинг       | Ruff                                |
| Тестування    | pytest + factory-boy                |

## Архітектура

```
apps/
├── core/           — Базові моделі, вибір мов (34 мови), винятки
├── users/          — Кастомна модель користувача (email-based), автентифікація
├── projects/       — Проєкти та мови проєктів
├── translations/   — Ключі та значення перекладів
├── integrations/   — Зовнішні інтеграції (placeholder)
└── factories/      — Тестові фабрики (factory-boy)
```

**Ключові архітектурні рішення:**

- **UUID первинні ключі** з `created_at` / `updated_at` на всіх моделях
- **Utils layer** для всієї бізнес-логіки (не у views, serializers чи model `save()`)
- **Input / output serializers** — явне розділення, без `ModelSerializer`
- **Slug-based URLs** для проєктів та крапкова нотація для ключів
- **LimitOffset пагінація** (за замовчуванням 20, максимум 100)

## Початок роботи

### Передумови

- Python 3.12+
- Docker та Docker Compose

### Швидкий старт (Docker)

```bash
cp .env.example .env
docker compose up --build
```

Застосунок буде доступний за адресами:

| Сервіс      | URL                                 |
| ----------- | ----------------------------------- |
| API         | http://localhost:8000/api/v1/       |
| Swagger UI  | http://localhost:8000/api/docs/     |
| ReDoc       | http://localhost:8000/api/schema/redoc/ |
| Адмінка     | http://localhost:8000/admin/        |

### Ручне налаштування

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver
```

### Наповнення бази даних

Наповнити базу тестовими даними (проєкти, ключі, переклади, адмін-користувач):

```bash
python manage.py seed_db
```

Команда **ідемпотентна** — повторний запуск пропускає вже існуючі об'єкти.

Щоб видалити всі seed-дані та створити заново:

```bash
python manage.py seed_db --flush
```

#### Що створюється

| Сутність       | Деталі                                         |
| -------------- | ---------------------------------------------- |
| Суперкористувач| `admin@admin.com` / `admin`                    |
| web-app        | 321 ключ, мови: en, uk, de, fr, es             |
| mobile-app     | 60 ключів, мови: en, uk, pl, ja                |
| marketing-site | 40 ключів, мови: en, uk, de, fr, es, pl        |

- Ключі мають 3-4 рівні вкладеності (напр. `auth.login.form.title`)
- Англійська (базова мова) перекладена на 100%
- Цільові мови мають ~20% навмисно неперекладених ключів
- Переклади псевдо-локалізовані: `[UK] Save`, `[DE] Loading...` тощо

### Змінні середовища

| Змінна                             | Опис                               | За замовчуванням         |
| ---------------------------------- | ---------------------------------- | ------------------------ |
| `DJANGO_SECRET_KEY`                | Секретний ключ Django              | —                        |
| `DJANGO_ALLOWED_HOSTS`             | Дозволені хости (через кому)       | `localhost,127.0.0.1`   |
| `DJANGO_SETTINGS_MODULE`           | Модуль налаштувань                 | `tms_backend.settings.local` |
| `CORS_ALLOWED_ORIGINS`             | CORS-джерела (через кому)          | —                        |
| `DATABASE_URL`                     | Рядок підключення PostgreSQL       | —                        |
| `REDIS_URL`                        | Рядок підключення Redis            | `redis://redis:6379/0`  |
| `JWT_ACCESS_TOKEN_LIFETIME_MINUTES`| TTL access-токена у хвилинах       | `60`                     |
| `JWT_REFRESH_TOKEN_LIFETIME_DAYS`  | TTL refresh-токена у днях          | `7`                      |
| `JWT_SIGNING_KEY`                  | Ключ підпису JWT (опціонально)     | `DJANGO_SECRET_KEY`      |

## Огляд API

Повна OpenAPI специфікація: [`docs/openapi.yaml`](docs/openapi.yaml)
Інтерактивна документація: [Swagger UI](http://localhost:8000/api/docs/) | [ReDoc](http://localhost:8000/api/schema/redoc/)

### Автентифікація

| Метод  | Ендпоінт                    | Опис                             |
| ------ | --------------------------- | -------------------------------- |
| POST   | `/api/v1/auth/token/`       | Отримати пару JWT токенів        |
| POST   | `/api/v1/auth/token/refresh/` | Оновити access-токен           |
| POST   | `/api/v1/auth/logout/`      | Вихід (blacklist refresh-токена) |

### Проєкти

| Метод  | Ендпоінт                                 | Опис                         |
| ------ | ---------------------------------------- | ---------------------------- |
| GET    | `/api/v1/projects/`                      | Список проєктів              |
| POST   | `/api/v1/projects/`                      | Створити проєкт              |
| GET    | `/api/v1/projects/{slug}/`               | Отримати проєкт              |
| PATCH  | `/api/v1/projects/{slug}/`               | Оновити проєкт               |
| DELETE | `/api/v1/projects/{slug}/`               | Видалити проєкт              |
| GET    | `/api/v1/projects/{slug}/export/`        | Експорт перекладів проєкту   |

### Мови

| Метод  | Ендпоінт                                          | Опис                        |
| ------ | ------------------------------------------------- | --------------------------- |
| GET    | `/api/v1/projects/{slug}/languages/`              | Список мов проєкту          |
| POST   | `/api/v1/projects/{slug}/languages/`              | Додати мову                 |
| PATCH  | `/api/v1/projects/{slug}/languages/{lang_code}/`  | Оновити мову                |
| DELETE | `/api/v1/projects/{slug}/languages/{lang_code}/`  | Видалити мову               |

### Ключі перекладів

| Метод  | Ендпоінт                                          | Опис                        |
| ------ | ------------------------------------------------- | --------------------------- |
| GET    | `/api/v1/projects/{slug}/keys/`                   | Список ключів               |
| POST   | `/api/v1/projects/{slug}/keys/`                   | Створити ключ               |
| GET    | `/api/v1/projects/{slug}/keys/{key_name}/`        | Отримати ключ               |
| PATCH  | `/api/v1/projects/{slug}/keys/{key_name}/`        | Оновити ключ                |
| DELETE | `/api/v1/projects/{slug}/keys/{key_name}/`        | Видалити ключ               |
| POST   | `/api/v1/projects/{slug}/keys/bulk-delete/`       | Масове видалення ключів     |

### Переклади

| Метод  | Ендпоінт                                                          | Опис                             |
| ------ | ----------------------------------------------------------------- | -------------------------------- |
| GET    | `/api/v1/projects/{slug}/keys/{key}/translations/`                | Список перекладів для ключа      |
| PATCH  | `/api/v1/projects/{slug}/keys/{key}/translations/`                | Пакетне створення/оновлення      |
| PUT    | `/api/v1/projects/{slug}/keys/{key}/translations/{lang_code}/`    | Створити або замінити переклад   |
| DELETE | `/api/v1/projects/{slug}/keys/{key}/translations/{lang_code}/`    | Видалити переклад                |

### Публічний доступ

| Метод  | Ендпоінт                                    | Опис                       |
| ------ | ------------------------------------------- | -------------------------- |
| GET    | `/api/v1/public/{slug}/translations/`       | Публічний експорт перекладів|

### Користувачі

| Метод  | Ендпоінт                           | Опис                        |
| ------ | ---------------------------------- | --------------------------- |
| GET    | `/api/v1/users/`                   | Список користувачів         |
| GET    | `/api/v1/users/{id}/`              | Деталі користувача          |
| GET    | `/api/v1/users/me/`                | Профіль поточного користувача|
| PATCH  | `/api/v1/users/me/`                | Оновити профіль             |
| POST   | `/api/v1/users/me/change-password/`| Змінити пароль              |

### Інфраструктура

| Метод  | Ендпоінт       | Опис           |
| ------ | -------------- | -------------- |
| GET    | `/api/health/` | Health check   |

## Схема бази даних

Повна діаграма сутностей та зв'язків — [docs/schema.md](docs/schema.md).

## Розгортання

### Docker Production

```bash
docker compose -f docker-compose.yml up -d --build
```

Скрипт `entrypoint.sh` автоматично:
1. Очікує готовність PostgreSQL
2. Запускає міграції бази даних
3. Збирає статичні файли

Gunicorn налаштований з **3 воркерами** та **120с таймаутом**.

### Змінні середовища для production

Окрім змінних, зазначених вище, налаштуйте для production:

```env
DJANGO_SECRET_KEY=<надійний-випадковий-ключ>
DJANGO_ALLOWED_HOSTS=yourdomain.com
CORS_ALLOWED_ORIGINS=https://yourdomain.com
CSRF_TRUSTED_ORIGINS=https://yourdomain.com
SECURE_SSL_REDIRECT=True
```

## Тестування

```bash
pytest                          # запустити всі тести
pytest --cov                    # запустити з coverage-звітом
pytest apps/translations/       # тести конкретного застосунку
```

- **Мінімальне покриття:** 80%
- **Стек:** pytest + factory-boy
- **Налаштування:** `tms_backend.settings.test`

## Якість коду

### Ruff

```bash
ruff check .                    # лінтинг
ruff format .                   # форматування
ruff check --fix .              # автовиправлення
```

### Pre-commit

```bash
pre-commit install
```

Налаштовані хуки:
- `trailing-whitespace`
- `end-of-file-fixer`
- `check-yaml`
- `check-json`
- `ruff` (лінтинг + автовиправлення)
- `ruff-format`
- `django-check-migrations`

Конфігураційні файли: [`pyproject.toml`](pyproject.toml), [`.pre-commit-config.yaml`](.pre-commit-config.yaml)

## Внесок у проєкт

Дивіться [CONTRIBUTING.md](CONTRIBUTING.md) для ознайомлення з настановами розробки та стандартами коду.

---

Built by [Roman Snitsarenko](https://github.com/OrdDreamer)
