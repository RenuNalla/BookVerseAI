# AI Book Translation Platform — Phase 1: Project Setup

## Stack
- **Backend:** Python, FastAPI, SQLAlchemy, Alembic, Celery, Redis
- **Frontend:** Angular 18 (standalone components) + Bootstrap 5
- **Database:** PostgreSQL
- **Infra:** Docker, Docker Compose, GitHub Actions

## Run everything with Docker (recommended)
```bash
cp backend/.env.example backend/.env
docker compose up --build
```
- Backend: http://localhost:8000/docs
- Frontend: http://localhost:4200
- Health check: http://localhost:8000/api/v1/health

## Run backend locally (without Docker)
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head   # creates the users table (Phase 2)
uvicorn app.main:app --reload
```

> Using Docker Compose? Run migrations once the `db` container is healthy:
> `docker compose exec backend alembic upgrade head`

## Run frontend locally (without Docker)
```bash
cd frontend
npm install
npm start
```

## Run backend tests
```bash
cd backend
pytest app/tests -v
```

## Phase 2 — Auth endpoints
| Method | Path | Auth required | Purpose |
|---|---|---|---|
| POST | `/api/v1/auth/register` | No | Create a user account |
| POST | `/api/v1/auth/login` | No | Exchange email+password for an access + refresh token pair |
| POST | `/api/v1/auth/refresh` | No (needs valid refresh token) | Exchange a refresh token for a new access token |
| GET | `/api/v1/auth/me` | Yes (Bearer access token) | Return the logged-in user's profile |

Frontend routes: `/login`, `/register` (public), `/library` (protected by `authGuard`). Google OAuth was left out of Phase 2 as originally scoped — flag if you want it added now or folded into a later phase, since it needs a registered OAuth client and redirect URI first.

## Phase 3 — Book upload
| Method | Path | Auth required | Purpose |
|---|---|---|---|
| POST | `/api/v1/books/upload` | Yes | Upload a PDF/EPUB/DOCX/TXT, validated and stored |
| GET | `/api/v1/books` | Yes | List the current user's books |
| GET | `/api/v1/books/{id}` | Yes | Fetch one book (owner-scoped) |

Storage defaults to `STORAGE_BACKEND=local` (writes to a Docker volume, zero AWS setup needed). Switch to `STORAGE_BACKEND=s3` and fill in `AWS_*` once you have a bucket + credentials — no application code changes needed, it's a one-line config swap (see `app/core/storage.py`).

Upload page (`/upload`) now does a real upload: drag-and-drop or file picker, client-side validation mirroring the backend's rules, a live progress bar, and a success message linking to the library.