# TMS Backend

Django REST API for centralized translation management across projects.

![Version](https://img.shields.io/badge/version-0.1.0-blue)
![Python 3.12](https://img.shields.io/badge/python-3.12-blue)
![Django 6.0](https://img.shields.io/badge/django-6.0-green)
![DRF 3.16](https://img.shields.io/badge/DRF-3.16-red)
![License: MIT](https://img.shields.io/badge/license-MIT-green)

[Українська версія README](README.uk.md)

## Roadmap

See [docs/ROADMAP.md](docs/ROADMAP.md) for planned features and priorities.

## Tech Stack

| Component     | Technology                          |
| ------------- | ----------------------------------- |
| Framework     | Django 6.0 + Django REST Framework  |
| Database      | PostgreSQL 16                       |
| Cache         | Redis 7                             |
| Auth          | JWT (simplejwt) with token blacklist|
| API Docs      | drf-spectacular (Swagger / ReDoc)   |
| Container     | Docker + Docker Compose             |
| CI/CD         | GitHub Actions                      |
| Linting       | Ruff                                |
| Testing       | pytest + factory-boy                |

## Architecture

```
apps/
├── core/           — Base models, language choices (34 languages), exceptions
├── users/          — Custom user model (email-based), authentication
├── projects/       — Projects and project languages
├── translations/   — Translation keys and values
├── integrations/   — External integrations (placeholder)
└── factories/      — Test factories (factory-boy)
```

**Key Design Decisions:**

- **UUID primary keys** with `created_at` / `updated_at` on all models
- **Utils layer** for all business logic (not in views, serializers, or model `save()`)
- **Input / output serializers** — explicit separation, no `ModelSerializer`
- **Slug-based URLs** for projects and dot-notation key names
- **LimitOffset pagination** (default 20, max 100)

## Getting Started

### Prerequisites

- Python 3.12+
- Docker & Docker Compose

### Quick Start (Docker)

```bash
cp .env.example .env
docker compose up --build
```

The app will be available at:

| Service     | URL                                 |
| ----------- | ----------------------------------- |
| API         | http://localhost:8000/api/v1/       |
| Swagger UI  | http://localhost:8000/api/docs/     |
| Admin       | http://localhost:8000/admin/        |

### Manual Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver
```

### Seed Database

Fill the database with development data (projects, keys, translations, admin user):

```bash
python manage.py seed_db
```

The command is **idempotent** — running it again skips already existing objects.

To wipe all seeded data and re-create from scratch:

```bash
python manage.py seed_db --flush
```

#### What gets created

| Entity         | Details                                        |
| -------------- | ---------------------------------------------- |
| Superuser      | `admin@admin.com` / `admin`                    |
| web-app        | 321 keys, languages: en, uk, de, fr, es        |
| mobile-app     | 60 keys, languages: en, uk, pl, ja             |
| marketing-site | 40 keys, languages: en, uk, de, fr, es, pl     |

- Keys have 3-4 levels of nesting (e.g. `auth.login.form.title`)
- English (base language) is 100% translated
- Target languages have ~20% of keys intentionally left untranslated
- Translations are pseudo-localized: `[UK] Save`, `[DE] Loading...`, etc.

### Environment Variables

| Variable                           | Description                        | Default                  |
| ---------------------------------- | ---------------------------------- | ------------------------ |
| `DJANGO_SECRET_KEY`                | Django secret key                  | —                        |
| `DJANGO_ALLOWED_HOSTS`             | Comma-separated allowed hosts      | `localhost,127.0.0.1`   |
| `DJANGO_SETTINGS_MODULE`           | Settings module                    | `tms_backend.settings.local` |
| `CORS_ALLOWED_ORIGINS`             | Comma-separated CORS origins       | —                        |
| `DATABASE_URL`                     | PostgreSQL connection string       | —                        |
| `REDIS_URL`                        | Redis connection string            | `redis://redis:6379/0`  |
| `JWT_ACCESS_TOKEN_LIFETIME_MINUTES`| Access token TTL in minutes        | `60`                     |
| `JWT_REFRESH_TOKEN_LIFETIME_DAYS`  | Refresh token TTL in days          | `7`                      |
| `JWT_SIGNING_KEY`                  | JWT signing key (optional)         | `DJANGO_SECRET_KEY`      |

## API Overview

Full OpenAPI specification: [`docs/openapi.yaml`](docs/openapi.yaml)
Interactive docs: [Swagger UI](http://localhost:8000/api/docs/) | [ReDoc](http://localhost:8000/api/schema/redoc/)

### Auth

| Method | Endpoint                    | Description                      |
| ------ | --------------------------- | -------------------------------- |
| POST   | `/api/v1/auth/token/`       | Obtain JWT token pair            |
| POST   | `/api/v1/auth/token/refresh/` | Refresh access token           |
| POST   | `/api/v1/auth/logout/`      | Logout (blacklist refresh token) |

### Projects

| Method | Endpoint                                 | Description                  |
| ------ | ---------------------------------------- | ---------------------------- |
| GET    | `/api/v1/projects/`                      | List projects                |
| POST   | `/api/v1/projects/`                      | Create a project             |
| GET    | `/api/v1/projects/{slug}/`               | Retrieve a project           |
| PATCH  | `/api/v1/projects/{slug}/`               | Update a project             |
| DELETE | `/api/v1/projects/{slug}/`               | Delete a project             |
| GET    | `/api/v1/projects/{slug}/export/`        | Export project translations  |

### Languages

| Method | Endpoint                                          | Description                 |
| ------ | ------------------------------------------------- | --------------------------- |
| GET    | `/api/v1/projects/{slug}/languages/`              | List project languages      |
| POST   | `/api/v1/projects/{slug}/languages/`              | Add a language              |
| PATCH  | `/api/v1/projects/{slug}/languages/{lang_code}/`  | Update a language           |
| DELETE | `/api/v1/projects/{slug}/languages/{lang_code}/`  | Remove a language           |

### Translation Keys

| Method | Endpoint                                          | Description                 |
| ------ | ------------------------------------------------- | --------------------------- |
| GET    | `/api/v1/projects/{slug}/keys/`                   | List translation keys       |
| POST   | `/api/v1/projects/{slug}/keys/`                   | Create a key                |
| GET    | `/api/v1/projects/{slug}/keys/{key_name}/`        | Retrieve a key              |
| PATCH  | `/api/v1/projects/{slug}/keys/{key_name}/`        | Update a key                |
| DELETE | `/api/v1/projects/{slug}/keys/{key_name}/`        | Delete a key                |
| POST   | `/api/v1/projects/{slug}/keys/bulk-delete/`       | Bulk delete keys            |

### Translations

| Method | Endpoint                                                          | Description                      |
| ------ | ----------------------------------------------------------------- | -------------------------------- |
| GET    | `/api/v1/projects/{slug}/keys/{key}/translations/`                | List translations for a key      |
| PATCH  | `/api/v1/projects/{slug}/keys/{key}/translations/`                | Batch create/update translations |
| PUT    | `/api/v1/projects/{slug}/keys/{key}/translations/{lang_code}/`    | Create or replace a translation  |
| DELETE | `/api/v1/projects/{slug}/keys/{key}/translations/{lang_code}/`    | Remove a translation             |

### Public

| Method | Endpoint                                    | Description                |
| ------ | ------------------------------------------- | -------------------------- |
| GET    | `/api/v1/public/{slug}/translations/`       | Public translations export |

### Users

| Method | Endpoint                           | Description                 |
| ------ | ---------------------------------- | --------------------------- |
| GET    | `/api/v1/users/`                   | List users                  |
| GET    | `/api/v1/users/{id}/`              | Retrieve user details       |
| GET    | `/api/v1/users/me/`                | Get current user profile    |
| PATCH  | `/api/v1/users/me/`                | Update current user profile |
| POST   | `/api/v1/users/me/change-password/`| Change password             |

### Infrastructure

| Method | Endpoint       | Description  |
| ------ | -------------- | ------------ |
| GET    | `/api/health/` | Health check |

## Database Schema

See [docs/schema.md](docs/schema.md) for the full entity-relationship diagram.

## Deployment

### Docker Production

```bash
docker compose -f docker-compose.yml up -d --build
```

The `entrypoint.sh` script automatically:
1. Waits for PostgreSQL to become ready
2. Runs database migrations
3. Collects static files

Gunicorn is configured with **3 workers** and a **120s timeout**.

### Production Environment Variables

In addition to the variables listed above, configure these for production:

```env
DJANGO_SECRET_KEY=<strong-random-key>
DJANGO_ALLOWED_HOSTS=yourdomain.com
CORS_ALLOWED_ORIGINS=https://yourdomain.com
CSRF_TRUSTED_ORIGINS=https://yourdomain.com
SECURE_SSL_REDIRECT=True
```

## Testing

```bash
pytest                          # run all tests
pytest --cov                    # run with coverage report
pytest apps/translations/       # run tests for a specific app
```

- **Coverage minimum:** 80%
- **Stack:** pytest + factory-boy
- **Settings:** `tms_backend.settings.test`

## Code Quality

### Ruff

```bash
ruff check .                    # lint
ruff format .                   # format
ruff check --fix .              # auto-fix
```

### Pre-commit

```bash
pre-commit install
```

Configured hooks:
- `trailing-whitespace`
- `end-of-file-fixer`
- `check-yaml`
- `check-json`
- `ruff` (lint + auto-fix)
- `ruff-format`
- `django-check-migrations`

Config files: [`pyproject.toml`](pyproject.toml), [`.pre-commit-config.yaml`](.pre-commit-config.yaml)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines and coding standards.

---

Built by [Roman Snitsarenko](https://github.com/OrdDreamer)
