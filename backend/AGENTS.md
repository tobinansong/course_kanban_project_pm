# Backend codebase notes

## Overview

This backend is a FastAPI app that serves a static frontend build at `/` (when available) and a JSON health check at `/api/health`. It is intended to be the API and static file host for the full application.

## Structure

- app/main.py: FastAPI app, static file hosting, and health endpoint.
- requirements.txt: Runtime dependencies for the backend service.

## Local run

Install dependencies and run the server locally:

- `pip install -r backend/requirements.txt`
- `uvicorn app.main:app --host 0.0.0.0 --port 8000`

## Docker

Docker build and run is managed from the repository root via docker compose.