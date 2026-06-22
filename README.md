# OrderFlow — Backend

FastAPI + SQLite backend for the OrderFlow internal order management system.

---

## Tech Stack

- **Python 3.12**
- **FastAPI** — HTTP framework, automatic OpenAPI docs
- **SQLite** — file-based database with WAL mode
- **pydantic-settings** — typed config from environment variables
- **python-jose** — JWT auth
- **bcrypt** — password hashing
- **uvicorn** — ASGI server

---

## Prerequisites

- Python 3.12+ — or — Docker Desktop

---

## 1. How to Install Dependencies

### Option 1 — Docker (Recommended)

Docker handles dependencies automatically. No manual install needed — skip to section 3.

### Option 2 — Manual

Create and activate a virtual environment, then install:

```bash
cd orderflow-backend

python3 -m venv .venv
source .venv/bin/activate      # macOS/Linux
.venv\Scripts\activate         # Windows

pip install -r requirements.txt
```

---

## 2. How to Set Up and Seed the Database

### Option 1 — Docker (Recommended)

Seeding happens automatically when the container starts. No extra steps needed — see section 3.

### Option 2 — Manual

A `.env` file is included in the repository for demo purposes. No configuration needed to run locally.

Run migrations and seed the database:

```bash
uvicorn app.main:app --port 8000
# migrations run automatically on startup, then stop the server and seed:

python seed.py
```

#### Verifying the seed was successful

You should see:

```
✓ Admin user created  (admin@orderflow.com / password)
✓ Seeded 500 orders successfully
```

If you see `already exists — skipping`, the data is already there from a previous run — this is fine.

**If seeding failed** (error or missing data):

```bash
# Wipe the database and re-seed from scratch
rm -f database/orderflow.db
python seed.py
```

The seed script is idempotent — running it multiple times is safe, it skips existing data.

---

## 3. How to Run the Backend

### Option 1 — Docker (Recommended)

A `.env` file is included in the repository for demo purposes. No configuration needed.

```bash
cd orderflow-backend
docker compose up
```

This will:
- Build the Python image (first time only)
- Install all dependencies
- Run database migrations automatically
- Seed the database with 1 admin user + 500 sample orders
- Start the API server on `http://localhost:8000`

> First time running and the image hasn't been built yet:
> ```bash
> docker compose up --build
> ```

#### Verifying the seed was successful

```bash
docker compose logs backend
```

You should see:

```
✓ Admin user created  (admin@orderflow.com / password)
✓ Seeded 500 orders successfully
```

**If seeding failed:**

```bash
# Re-run seed inside the running container
docker compose exec backend python seed.py

# Or if the container stopped
docker compose run --rm backend python seed.py

# Wipe and start fresh
docker compose down
rm -f database/orderflow.db
docker compose up --build
```

#### Stop the server

```bash
docker compose down
```

### Option 2 — Manual

```bash
uvicorn app.main:app --reload --port 8000
```

Migrations run automatically on startup — the `database/` folder and `.db` file are created if they don't exist.

The API is available at `http://localhost:8000`.

---

## 4. How to Run the Frontend

See the frontend README at `orderflow-ui/README.md` for full setup instructions.

Quick start:

```bash
cd orderflow-ui
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`. Requires the backend to be running first.

---

## 5. How to Run Tests

```bash
# Ensure your virtual environment is active (Option 2 only)
pytest

# With verbose output
pytest -v

# Specific test file
pytest tests/test_orders.py -v
pytest tests/test_auth.py -v
pytest tests/test_status_transitions.py -v
```

Tests use an in-memory SQLite database — no test data is written to disk and no running server is needed.

---

## Default Login Credentials

```
Email:    admin@orderflow.com
Password: password
```

---

## Interactive API Docs

FastAPI automatically generates live, interactive documentation from the code — no separate doc files to maintain.

### Production

The API is deployed on AWS EC2 and accessible at:

| | URL | Description |
|---|---|---|
| Swagger UI | `http://13.247.70.10:8000/docs` | Interactive — run requests directly from the browser |
| ReDoc | `http://13.247.70.10:8000/redoc` | Clean read-only reference |

### Local

Once the server is running locally, open either of these in your browser:

| | URL | Description |
|---|---|---|
| Swagger UI | `http://localhost:8000/docs` | Interactive — run requests directly from the browser |
| ReDoc | `http://localhost:8000/redoc` | Clean read-only reference |

---

## API Reference

### Endpoints Summary

| Method | Endpoint | Authentication Required | Description |
|--------|----------|------------------------|-------------|
| `GET` | `/health` | No | Health check |
| `POST` | `/api/auth/login` | No | Login, returns JWT |
| `GET` | `/api/orders` | Yes | List orders (paginated, filterable) |
| `POST` | `/api/orders` | Yes | Create a new order |
| `GET` | `/api/orders/{id}` | Yes | Get order by ID |
| `PATCH` | `/api/orders/{id}/status` | Yes | Update order status |
| `GET` | `/api/orders/{id}/history` | Yes | Get status change history |
| `GET` | `/api/dashboard/summary` | Yes | Dashboard metrics |
| `GET` | `/api/reports/summary` | Yes | Reports with date range filter |

### Order Query Params

```
GET /api/orders?page=1&page_size=20&status=pending&search=john&date_from=2025-01-01&date_to=2025-01-31
```

### Order Lifecycle

```
pending → paid → shipped
pending → cancelled
paid    → cancelled
```

Any other transition returns `400 Bad Request`.

---

## Stretch Goals Completed

The assessment listed the following as optional extras. All three were implemented:

| Stretch Goal | Implemented | Details |
|---|---|---|
| Status history / audit trail | Yes | Every status change is recorded in `order_status_history` table with `from_status`, `to_status`, and `changed_at`. Exposed via `GET /api/orders/{id}/history`. Visible on the order detail page as a full chronological timeline. |
| Additional dashboard metrics | Yes | Total revenue, average order value, orders today, 7-day orders-per-day chart with hover tooltip. |
| Reports page | Yes | 30-day (or custom date range) trend chart with bar/line toggle, cancellation rate, avg fulfilment days, peak day, top 5 customers, revenue vs previous month. |

---

## Architecture

```
Request → Routes → Services → Repositories → SQLite
```

- **Routes** (`app/routes/`) — HTTP layer, Pydantic validation, calls services
- **Services** (`app/services/`) — business logic, status transition rules
- **Repositories** (`app/repositories/`) — raw SQL queries, no business logic
- **Schemas** (`app/schemas/`) — Pydantic models for request/response shapes
- **Database** (`app/database/`) — SQLite connection, migrations runner

### Key Decisions

- **Raw SQL over ORM** — demonstrates SQL competence, full control over queries
- **Offset pagination** — simple page/page_size pattern suits the use case
- **Optimistic locking** — `UPDATE ... WHERE status = ?` prevents race conditions on status updates
- **Migrations on startup** — SQL files in `database/` run via FastAPI `lifespan` event
- **Single admin user** — no RBAC needed per assessment scope
- **WAL mode** — SQLite Write-Ahead Logging for concurrent reads

---

## 6. Assumptions & Trade-offs

- Single admin user — the assessment does not require multi-user or RBAC
- JWT tokens expire after 24 hours (1440 minutes) — no refresh token implemented
- SQLite is sufficient for the expected ~100k orders/month volume with proper indexing
- No rate limiting — would add in production
- CORS is configured to allow `localhost:5173`, `localhost:4173`, and the deployed Vercel frontend — see `docker-compose.yml`
- A `.env` file is included in the repository intentionally for demo/assessment purposes — in a real project this would be in `.gitignore`
- Environment variables are set directly in `docker-compose.yml` for the production EC2 deployment so the container is fully self-contained without relying on a `.env` file at runtime

---

## 7. Areas I Would Improve With More Time

- Add refresh token support
- Add rate limiting middleware
- Paginate the status history endpoint
- Add `date_from` / `date_to` format validation as a reusable FastAPI dependency
- Add integration tests for the reports endpoint
- Switch to PostgreSQL for higher-volume production deployment

---

## 8. Production Deployment Notes

### Current Deployment (Simple — for demo/testing purposes only)

The backend is deployed directly on an **AWS EC2 instance** running Docker. This was intentionally kept simple for the purposes of this assessment:

- Docker image is built and run directly on the EC2 instance via `docker compose up`
- Environment variables are hardcoded in `docker-compose.yml`
- The server is exposed on port `8000` over plain `http://` — **no HTTPS, no load balancer**
- The `.env` file is committed to the repository — **not secure for a real project**
- Secrets such as `JWT_SECRET` are not managed securely

> This setup is **not production-grade** and was used purely for demo convenience.

---

### Proper Production Deployment (What I Would Do)

With more time and for a real production system I would replace the above with a fully managed AWS setup:

| Component | Service | Reason |
|---|---|---|
| Container registry | **Amazon ECR** | Store and version Docker images securely, integrated with AWS IAM |
| Container orchestration | **Amazon ECS (Fargate)** | Run containers without managing EC2 instances, auto-scaling built in |
| Load balancer | **Application Load Balancer (ALB)** | HTTPS termination, health checks, zero-downtime deployments |
| Secret management | **AWS Secrets Manager** | Store `JWT_SECRET`, DB credentials — never in code or `docker-compose.yml` |
| Database | **Amazon RDS (PostgreSQL)** | Managed, scalable, automated backups — replaces SQLite at higher volume |
| CI/CD | **GitHub Actions → ECR → ECS** | Auto-deploy on push to main, no manual SSH needed |

#### Deployment flow with the above setup

```
GitHub push
  → GitHub Actions builds Docker image
  → Pushes image to ECR
  → Updates ECS service with new task definition
  → ALB routes HTTPS traffic to healthy ECS tasks
  → Secrets Manager injects JWT_SECRET and DB credentials at runtime
```

This would give HTTPS out of the box, horizontal scaling as user load increases, zero hardcoded secrets, and full audit trails via CloudTrail.
