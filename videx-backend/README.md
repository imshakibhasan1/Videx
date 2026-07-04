# VIDEX Backend

> AI-Powered Video Reverse-Engineering Platform

This is the FastAPI backend for VIDEX, handling video analysis via MiMo V2.5 and prompt generation for Text-to-Video models.

## 🚀 Architecture Highlights

- **FastAPI**: Async web framework serving the REST API.
- **PostgreSQL**: Primary datastore, accessed via SQLAlchemy 2.0 (asyncpg).
- **Redis & Celery**: Background task processing for video analysis and prompt generation.
- **Server-Sent Events (SSE)**: Real-time updates pushed to the frontend via Redis Pub/Sub.
- **Cloudinary**: Secure direct client-to-CDN uploads via signed URLs.
- **MiMo V2.5**: Core AI engine for omnimodal video understanding.

## 🛠️ Local Development Setup

### 1. Requirements
- Python 3.12+
- Docker & Docker Compose
- Hatch (for dependency management)

### 2. Environment Variables
Copy the template and fill in the secrets (especially Cloudinary and MiMo API keys):
```bash
cp .env.example .env
```

### 3. Run with Docker Compose
The easiest way to start the entire stack (Postgres, Redis, API, Celery Worker):
```bash
docker compose up -d --build
```
The API will be available at `http://localhost:8000`.

### 4. Local Development (without Docker for API)
If you prefer running the API directly on your host for debugging:

1. Start dependencies:
   ```bash
   docker compose up -d db redis
   ```
2. Install dependencies:
   ```bash
   pip install hatch
   hatch env create
   hatch shell
   ```
3. Run migrations (or create tables on startup if configured):
   ```bash
   alembic upgrade head
   ```
4. Start the API:
   ```bash
   uvicorn app.main:app --reload
   ```
5. Start the Celery Worker (in a separate terminal):
   ```bash
   celery -A app.tasks.celery_app worker --loglevel=info -Q analysis,prompts
   ```

## 🧪 Testing

Run the test suite using pytest:
```bash
pytest
```
Tests use a separate test database (`videx_test`) defined in `pyproject.toml`.

## 📚 API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/api/docs`
- ReDoc: `http://localhost:8000/api/redoc`
