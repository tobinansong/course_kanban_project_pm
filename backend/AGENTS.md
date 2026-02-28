# Backend codebase notes

## Overview

This backend is a FastAPI app that serves a static frontend build at `/` (when available), exposes a health check at `/api/health`, and provides CRUD-style endpoints for the Kanban board. It is intended to be the API and static file host for the full application.

## Structure

- app/main.py: FastAPI app, static file hosting, health endpoint, and board APIs.
- app/db.py: SQLite initialization and seed data.
- app/repository.py: Board data access and mutations.
- app/schemas.py: Pydantic request/response models.
- requirements.txt: Runtime dependencies for the backend service.

## Local run

Install dependencies and run the server locally:

- `pip install -r backend/requirements.txt`
- `uvicorn app.main:app --host 0.0.0.0 --port 8000`

## Docker

Docker build and run is managed from the repository root via docker compose.