# WorkSphere

WorkSphere is a production-oriented workplace management platform with authentication, RBAC, organization management, attendance, leave, calendar, projects, tasks, meetings, MOM, collaboration, knowledge documents, deterministic work planning, timelines, reports, and audit logging.

## Requirements

Docker Desktop is recommended. For local execution without Docker, install Python 3.12+, Node.js 20+, PostgreSQL, and Redis.

## Setup

```bash
cp .env.example .env
# Replace POSTGRES_PASSWORD and JWT_SECRET_KEY with unique generated values.
# Generate URL-safe secrets with:
openssl rand -hex 32
docker compose up --build
```

The frontend is at http://localhost:3000, API documentation at http://localhost:8000/docs, and the health endpoint is http://localhost:8000/api/v1/health. Set `NEXT_PUBLIC_API_URL` to the browser-accessible API URL before building the frontend image. PostgreSQL and Redis are not published to the host, and Redis is isolated from the frontend on a private Compose network. Terminate HTTPS at a reverse proxy or load balancer.

The API exposes:

- `GET /api/v1/health` for process health
- `GET /api/v1/health/ready` for PostgreSQL and Redis readiness
- `GET /docs` for OpenAPI documentation (disable or protect this endpoint in hardened production deployments)

For local development:

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload

cd ../frontend
npm install
npm run dev
```

Run the backend tests with the development requirements:

```bash
cd backend
pip install -r requirements-dev.txt
pytest
```

## Environment variables

See [.env.example](.env.example). Secrets and connection strings must be supplied through `.env` or the deployment environment; no credentials are committed.

## Production operations

Apply migrations before serving traffic:

```bash
docker compose up -d postgres redis
docker compose run --rm backend alembic upgrade head
docker compose up -d backend frontend
```

Create a PostgreSQL backup using the deployment script:

```bash
./scripts/backup-database.sh
```

Set `ENVIRONMENT=production`, a unique `JWT_SECRET_KEY` of at least 32 characters,
restricted `CORS_ORIGINS`, explicit `ALLOWED_HOSTS`, and a strong unique
`POSTGRES_PASSWORD`. Store backups outside the application host and test restores
regularly. The script writes private custom-format dumps to `backups/` by default;
pass a directory as its first argument to choose another destination. Run the
GitHub Actions workflow before deploying.

The intelligence layer is deterministic by design. No AI provider or model is
hard-coded into business workflows.
