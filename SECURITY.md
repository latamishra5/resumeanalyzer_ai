# Security Policy

## Supported Versions

Security fixes are maintained on the `main` branch for the current release.

## Security Architecture Highlights

- **Frontend / Admin Separation**: Public user routes ([app.py](app.py) / `frontend/`) do not expose admin login controls, audit logs, or multi-user database exports. Administrative operations run strictly in the isolated backend console (`backend/admin/app.py`).
- **Password Storage**: User and admin passwords are hashed using salted `scrypt` (`backend/auth/security.py`), with constant-time comparisons (`hmac.compare_digest`) and automatic transparent upgrades for legacy hashes.
- **Database Queries**: Parameterized SQLAlchemy Core queries (`backend/database/db.py`) protect against SQL injection on both SQLite and PostgreSQL.
- **XSS / HTML Hardening**: Dynamic inputs, AI output cards, and scraped job fields are escaped via `html.escape(..., quote=True)` and URL-scheme validated (`http`/`https`).
- **Secret Management**: API keys (`GOOGLE_API_KEY`, `OPENROUTER_API_KEY`) and optional `ADMIN_EMAIL` / `ADMIN_PASSWORD` or `DATABASE_URL` must only be configured via environment variables or untracked `.env` files—never committed to version control.

## Reporting a Vulnerability

If you discover a security issue:

1. **Do not** open a public GitHub issue containing exploit details or credentials.
2. Report it privately to the repository maintainer with reproduction steps, affected component/file, and impact assessment.
3. Rotate any potentially exposed API keys or database credentials immediately.
