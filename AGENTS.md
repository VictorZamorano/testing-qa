# AGENTS.md

Django 6.1.2 + DRF 3.18.3 + SimpleJWT task manager ("Gestor de tareas"). Python 3.15.2. Use the venv interpreter (`.\venv\Scripts\python.exe`) rather than bare `python`. Project text, UI, API messages, and identifiers are Spanish — keep new ones consistent.

## Commands

    .\venv\Scripts\python.exe manage.py migrate
    .\venv\Scripts\python.exe manage.py runserver          # http://localhost:8000/
    .\venv\Scripts\python.exe manage.py test               # 12 tests, all in tareas/tests.py
    .\venv\Scripts\python.exe manage.py test tareas.tests.GestionTareasAdminTests.test_admin_crea_tarea_para_otro_usuario

No CI, lint, formatter, typecheck, or pre-commit config exists — don't invent one. Scattered `pyright: ignore` comments exist but there is no pyright config.

## Gotchas

- `requirements.txt` is **UTF-16 LE with BOM** (`FF FE`), not UTF-8. Preserve that encoding when editing it (`Get-Content -Encoding Unicode`); a normal write will corrupt the dependency list.
- `db.sqlite3` is **tracked** (`.gitignore` has `# db.sqlite3` commented out) and ships with users `admin`/`admin` and `usuario2`/`usuario2`. Don't assume a clean DB or commit local data changes.
- `admin` is recreated on **every** `migrate`, including the test DB, by a `post_migrate` signal in `tareas/apps.py`. Other seed users exist only in the committed dev DB, so tests never see them.
- Tests authenticate by `RefreshToken.for_user(u).access_token` + `HTTP_AUTHORIZATION: Bearer ...`; they use a fresh test DB, so don't rely on committed data.
- Django writes test progress to stderr; in PowerShell with `2>&1` this can look like a failing native command / exit 1 even when the run ends `OK`. Check the `OK` line, not the PowerShell error styling.
- Email backend is **console** (prints to terminal, no SMTP).

## Architecture and conventions

- Only two packages: `gestor_tareas/` (settings, root URLs) and `tareas/` (the sole app: models, API views, serializers, permissions, templates, static JS).
- Custom user model `tareas.Usuario` (`AUTH_USER_MODEL`) with `rol` ∈ {`administrador`, `usuario`}. Use `get_user_model()` / `settings.AUTH_USER_MODEL`, never `django.contrib.auth.models.User`.
- Authorization is by `rol`, not Django `is_staff`/model permissions: `EsAdministrador` in `permissions.py` and `_es_administrador()` in `views.py`.
- Global DRF defaults are `JWTAuthentication` + `IsAuthenticated`; public endpoints opt out with `AllowAny` (`/api/login/`, `/api/register/`). Note `/api/token/` and `/api/token/refresh/` are SimpleJWT built-ins wired in `gestor_tareas/urls.py`, not in the app URLconf — README documents `/api/token/`, but `/api/login/` is a custom view that also returns user data.
- JWT: access 15m, refresh 1d, rotation + blacklist on; `rest_framework_simplejwt.token_blacklist` is installed, so `migrate` must run before `/api/logout/` works. The frontend stores tokens in `localStorage`, refreshes once on 401, and blacklists on logout.
- Task ownership rules (enforced in `views.py`, covered by tests — preserve when editing): admins see all tasks and may assign to any **active** user via `usuario_id`; normal users see only their own and get 403 if they pass `usuario_id`, 404 for an inactive target, 400 for a non-integer id. `detalle_tarea` filters by `usuario=request.user`, so even admins get 404 on others' tasks for detail/PATCH/DELETE. `usuario` is read-only in `TareaSerializer`, so PATCH cannot reassign ownership.
- Only migration is `tareas/migrations/0001_initial.py`; no fixtures or custom management commands.
