# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Coding standards

- Keep it simple. No over-engineering, no unnecessary defensive programming, no extra features.
- Use latest versions of libraries and idiomatic approaches.
- No emojis, ever.
- When hitting issues, identify the root cause with evidence before attempting a fix.

## Color scheme

- Accent Yellow: `#ecad0a`
- Blue Primary: `#209dd7`
- Purple Secondary: `#753991`
- Dark Navy: `#032147`
- Gray Text: `#888888`

## Commands

### Docker (primary workflow)

```bash
# Start the full app (builds frontend, packages into container)
docker compose up --build

# Using platform scripts from repo root
scripts/start-windows.ps1   # Windows
scripts/start-mac.sh        # macOS
scripts/start-linux.sh      # Linux
```

### Frontend (from `frontend/`)

```bash
npm run dev           # Next.js dev server (frontend only, no backend)
npm run build         # Static export to frontend/out/
npm run lint          # ESLint
npm run test          # Run unit tests (vitest)
npm run test:unit     # Same as test
npm run test:e2e      # Playwright e2e tests
npm run test:all      # Unit + e2e
```

Run a single unit test file:
```bash
npx vitest run src/components/KanbanBoard.test.tsx
```

### Backend (from `backend/`)

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Run Python tests
pytest
pytest tests/test_ai.py   # single file
```

## Architecture

### Request flow

The FastAPI backend serves the compiled Next.js static export at `/` and provides a REST API under `/api/`. In production (Docker), the frontend is compiled into `backend/app/static/` so everything runs from a single process on port 8000. In development, run the frontend dev server (`npm run dev`) and backend separately.

### Backend (`backend/app/`)

| File | Purpose |
|---|---|
| `main.py` | FastAPI app, all route definitions, static file mounting |
| `db.py` | SQLite init, schema, seed data; DB path defaults to `app/data/pm.db` (override with `PM_DB_PATH`) |
| `repository.py` | All DB reads/writes; raises typed errors (`BoardNotFoundError`, `CardNotFoundError`, `ColumnNotFoundError`) |
| `schemas.py` | Pydantic models for requests, responses, and AI operations |
| `ai.py` | OpenRouter HTTP client; `run_prompt()` and `run_structured_prompt()` |
| `ai_ops.py` | Dispatches AI-returned operations to repository functions |

AI calls go via OpenRouter using model `openai/gpt-oss-120b:free`. Requires `OPENROUTER_API_KEY` in `.env` at the repo root.

### AI structured output flow

`POST /api/ai/structured` accepts `{message, history}`, fetches current board state, sends it all to OpenRouter, parses the JSON response into `AiStructuredOutput` (Pydantic), then calls `apply_ai_operations()` to execute each operation against the DB. The AI response schema is a discriminated union on `type`: `rename_column`, `create_card`, `update_card`, `move_card`, `delete_card`.

### Frontend (`frontend/src/`)

| Path | Purpose |
|---|---|
| `app/page.tsx` | Root page; renders `KanbanBoard` |
| `components/KanbanBoard.tsx` | Main stateful component; fetches board from API, handles all mutations with optimistic updates |
| `lib/kanbanApi.ts` | All API calls to backend (`getBoard`, `createCard`, `moveCard`, `sendStructuredChat`, etc.) |
| `lib/kanban.ts` | Board data types and in-memory card move logic |
| `components/AiChatSidebar.tsx` | AI chat sidebar; calls `sendStructuredChat`, applies returned operations to board state |

Board state shape: `{ columns: Column[], cards: Record<string, Card> }` where columns hold ordered `cardIds`.

Drag-and-drop uses `@dnd-kit`. Next.js is configured for static export (`output: "export"`), so no server-side rendering — all API calls are client-side fetches to the same origin.

### Database

SQLite with tables: `users`, `boards`, `columns`, `cards`. Seeded on first run with one hardcoded user (`user`/`password`) and one board with 5 columns. Authentication is client-side only (localStorage) — the backend has no auth middleware.
