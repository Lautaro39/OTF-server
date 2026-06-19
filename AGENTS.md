# OTF-server — Project Context

## Overview

Django 6.0 + Django REST Framework 3.17 backend for the **One-Through-Five** Flutter app
(`../One-Through-Five`). The Flutter app is a community incident-reporting platform
(denuncias / complaints).

**Stack:** Python 3.14, Django 6.0.6, DRF 3.17.1, PostgreSQL (psycopg2-binary),
environs for config.

## Project structure

```
OTF-server/
├── AGENTS.md                          ← this file
├── requirements.txt                   ← django, djangorestframework, environs, psycopg2-binary
├── .venv/                             ← venv (created by `python3 -m venv .venv`)
├── backend_otf/
│   ├── manage.py
│   ├── backend_otf/
│   │   ├── settings.py
│   │   ├── urls.py
│   │   ├── wsgi.py / asgi.py
│   └── api/
│       ├── models.py                  ← 18 models (Usuario extends AbstractUser)
│       ├── serializers.py             ← DRF serializers for all models + auth serializers for Flutter
│       ├── views.py                   ← auth views (Login, Register, ProfileUpdate) + stub index
│       ├── urls.py                    ← denuncia/ routes
│       ├── auth_urls.py               ← auth/ routes (login, register, upload)
│       ├── admin.py                   ← Django admin registrations
│       └── migrations/                ← 0001_initial (fresh, reset 2026-06-19)
```

## Setup on a new machine

```bash
# 1. Venv
python3 -m venv .venv
source .venv/bin/activate

# 2. Dependencies
pip install -r requirements.txt

# 3. PostgreSQL (database: backend_otf, user: backend_otf, password: backend_otf)
#    Set host/port in backend_otf/.env:
#      DB_NAME=backend_otf
#      DB_USER=backend_otf
#      DB_PASSWORD=backend_otf
#      DB_HOST=localhost
#      DB_PORT=5432
createdb -U postgres backend_otf -O backend_otf

# 4. Migrate
cd backend_otf
python manage.py migrate

# 5. Run
python manage.py runserver 0.0.0.0:8000
```

## Architecture decisions

- **`Usuario` extends Django's `AbstractUser`** — full Django auth (password hashing,
  token generation, admin login). `AUTH_USER_MODEL = 'api.Usuario'`.
- **`USERNAME_FIELD = 'email'`** — login is by `email` + `password`. The Flutter app
  generates emails as `{DNI}@otf.com`, so in practice login = DNI + password.
- **Token auth via `rest_framework.authtoken`** — `TokenAuthentication` is the default
  auth class. Tokens are created on login/register, sent as `Authorization: Token <key>`.
- **DNI-based ID** — users register with their DNI, which becomes the email prefix.
- **Email moved to `Usuario`** — `email` lives on `Usuario` (auth model), not on
  `InfoUsuario`. `InfoUsuario` now only holds `dni`, `telefono`, `domicilio`.
- **`first_name` / `last_name`** added to `Usuario` (from `AbstractUser`), mapped to
  Flutter's `name` / `lastname`.
- **Roles stripped** — the Flutter `UserModel` expected `roles: [RoleModel]` but this app
  is user-only; `UserResponseSerializer` does not include roles.
- **`image` returns `null`** — no avatar/image field exists yet.
- **`Username` field** — auto-set to the email prefix (part before `@`) during
  registration.

## Active API endpoints

**Base URL:** `http://{host}:8000`

| Method | Path | Auth | Request body | Response (200/201) |
|--------|------|------|-------------|-------------------|
| `GET` | `/denuncia/` | No | — | `"Hello, world..."` (stub) |
| `POST` | `/auth/login/` | No | `{"email":"12345@otf.com","password":"..."}` | `{"user":{...},"token":"..."}` |
| `POST` | `/auth/register/` | No | `{"name":"Juan","lastname":"Perez","email":"12345@otf.com","phone":"...","dni":"12345","password":"..."}` | `{"user":{...},"token":"..."}` |
| `PUT` | `/auth/upload/<id>/` | Token | `{"name":"...","lastname":"...","phone":"..."}` (JSON or multipart) | `{"id":1,"name":"...","lastname":"...","email":"...","phone":"...","dni":"...","image":null}` |

**Flutter `UserModel` response shape** (returned in `user` field):
```json
{
  "id": 1,
  "name": "Juan",
  "lastname": "Perez",
  "email": "12345678@otf.com",
  "phone": "+5491112345678",
  "dni": "12345678",
  "image": null
}
```

## Data models (key entities)

| Model | Table | Purpose |
|-------|-------|---------|
| `Usuario` (AbstractUser) | `Usuarios` | Auth user; login by email; has first_name, last_name, email, password |
| `InfoUsuario` | `InfoUsuarios` | Extended info (1:1): dni, telefono, domicilio |
| `Denuncia` | `Denuncias` | Complaint/report: FK to Usuario, Categoria, Estado; titulo, descripcion |
| `Categoria` | `Categorias` | Category of complaint |
| `Estado` | `Estados` | Status catalog |
| `Voto` | `Votos` | User vote on a complaint |
| `Archivo` / `CarpetaArchivo` | `Archivos` / `CarpetaArchivos` | File attachments |
| `LogAcceso`, `AuditCambio`, `Notificacion` | — | Logging/audit/notifications |
| `Rol`, `UsuarioRol`, `Administrador` | — | Role system (unused by Flutter) |
| `TagDenuncia`, `DenunciaTag` | — | Tagging system |
| `TelefonoUsuario`, `PreferenciaUsuario` | — | Auxiliary tables |

All models have `db_column` Spanish-named columns mapped to English Django field names.
See `api/models.py:1-410` for full definitions.

## Serializers (non-auth)

All 18 models have DRF `ModelSerializer` classes in `api/serializers.py`.
`Denuncia` has three variants: `DenunciaListSerializer` (with human-readable labels),
`DenunciaDetailSerializer` (nested objects), `DenunciaWriteSerializer` (IDs only).

## What's NOT done yet

1. **No DRF views for the core models** — `Denuncia`, `Voto`, `Archivo`, etc. have
   serializers but no CRUD views. The Flutter app currently stores reports **locally**
   in SQLite. These need to be wired up so the app syncs to the backend.
2. **The Flutter `report_page_tab.dart`** currently writes to local SQLite — it needs
   updated to POST reports to the backend.
3. **`ALLOWED_HOSTS = []`** — must be configured for production.
4. **`DEBUG = True`** — must be set to `False` in production.
5. **No test suite** — `api/tests.py` is a placeholder.

## Key file reference

| File | Lines | What's in it |
|------|-------|-------------|
| `backend_otf/api/models.py` | 1–410 | All 18 Django models |
| `backend_otf/api/serializers.py` | 1–~360 | All serializers + auth serializers |
| `backend_otf/api/views.py` | 1–~60 | `LoginView`, `RegisterView`, `ProfileUpdateView`, `index` |
| `backend_otf/api/auth_urls.py` | 1–10 | `login/`, `register/`, `upload/<pk>/` |
| `backend_otf/api/urls.py` | 1–7 | `denuncia/` routes (just `index`) |
| `backend_otf/api/admin.py` | 1–45 | Django admin registrations |
| `backend_otf/backend_otf/settings.py` | 1–~140 | Django config + `AUTH_USER_MODEL`, `REST_FRAMEWORK` |
| `backend_otf/backend_otf/urls.py` | 1–25 | Root URL patterns: `auth/`, `denuncia/`, `admin/` |
| `backend_otf/api/migrations/0001_initial.py` | — | Fresh initial migration (reset 2026-06-19) |

## Running commands

```bash
source .venv/bin/activate
cd backend_otf

# Check for issues
python manage.py check

# Migrate
python manage.py migrate

# Run server
python manage.py runserver 0.0.0.0:8000

# Create superuser (for Django admin)
python manage.py createsuperuser
```
