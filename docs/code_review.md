# Code review

Review of the full codebase as of Part 10 (AI sidebar implemented, not yet committed).
Two bugs were found and fixed during the test run that triggered this review — they are included below as resolved items.

---

## Bugs

### FIXED — `move_card` UNIQUE constraint violation (backend)

**File:** `backend/app/repository.py`

In the cross-column move path, `move_card` updated only `column_id` while leaving `position` unchanged. If the card's old position coincided with an existing card's position in the target column, SQLite's `UNIQUE INDEX ON cards(column_id, position)` fired immediately — before `_reindex_column` could correct the positions. The same problem existed inside `_reindex_column` itself: assigning positions 0, 1, 2... one row at a time collides with rows that already hold those positions mid-loop.

Fix applied:
- The cross-column `UPDATE` now also sets `position = len(to_cards)`, a slot guaranteed to be free.
- `_reindex_column` now does a two-phase update: first shift all cards to `index + 1_000_000`, then assign final positions.

### FIXED — `vi.mock` hoisting crash in `KanbanBoard.test.tsx` (frontend)

**File:** `frontend/src/components/KanbanBoard.test.tsx`

The `vi.mock("@/lib/kanbanApi")` factory referenced `initialData`, which is a top-level import. Vitest hoists `vi.mock` calls above all imports, so `initialData` was not yet initialized when the factory ran, causing `ReferenceError: Cannot access '__vi_import_4__' before initialization`.

Fix applied: factory now uses `vi.fn()` for `getBoard` and `mockResolvedValue(initialData)` is set in `beforeEach`, after imports are resolved.

---

## Open issues

### Backend

**1. `create_card` position calculation is wrong when a column has one card at position 0**

`backend/app/repository.py:109`

```python
next_position = (position_row["max_position"] or -1) + 1
```

`or -1` treats `0` as falsy. If the column has exactly one card at position 0, `MAX(position)` returns `0`, and `(0 or -1) + 1 = 0` — assigning the new card position 0, which violates the UNIQUE constraint and raises an `IntegrityError`. The fix is an explicit `None` check:

```python
max_pos = position_row["max_position"]
next_position = (max_pos if max_pos is not None else -1) + 1
```

**2. Deprecated `on_event` in `main.py`**

`backend/app/main.py:48`

`@app.on_event("startup")` is deprecated in FastAPI. FastAPI emits a `DeprecationWarning` on startup. Replace with a lifespan context manager:

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(lifespan=lifespan)
```

**3. `test_ai.py` fails noisily when key is absent instead of skipping**

`backend/tests/test_ai.py:12`

```python
if not api_key:
    raise AssertionError("OPENROUTER_API_KEY must be set for live OpenRouter test")
```

A bare `AssertionError` shows as a test failure, not a skip. This confuses a CI run that lacks the key. Use `pytest.skip` instead:

```python
if not api_key:
    pytest.skip("OPENROUTER_API_KEY not set")
```

**4. `update_card` cannot clear details**

`backend/app/repository.py:130`

```python
next_details = details.strip() if details and details.strip() else existing["details"]
```

Sending `details=""` silently preserves the old value. This is inconsistent with `create_card`, which substitutes `"No details yet."`. The intended behaviour should be explicit (either always require a non-empty value and return 422, or allow clearing).

**5. `/api/chat` debug endpoint left in production code**

`backend/app/main.py:174`

`POST /api/chat` was scaffolded in Part 8 to verify OpenRouter connectivity. It is not used by the frontend and exposes an unnecessary API call. Remove it.

**6. No authentication on any API endpoint**

The backend has no auth middleware. Any process with network access to port 8000 can read or mutate the board. This is acceptable for a local Docker deployment but should be noted as a known gap if the app is ever exposed beyond localhost.

---

### Frontend

**7. Column rename fires an API call on every keystroke**

`frontend/src/components/KanbanColumn.tsx:44`

```tsx
onChange={(event) => onRename(column.id, event.target.value)}
```

`handleRenameColumn` in `KanbanBoard.tsx` immediately calls `renameColumn(columnId, title)` on each character. Rapid typing produces many sequential API calls; any failure triggers a full board refresh mid-typing. Add debouncing or switch to submit-on-blur.

**8. AI chat message list does not auto-scroll to latest message**

`frontend/src/components/AiChatSidebar.tsx:60`

The messages container uses `overflow-y-auto` but has no `useEffect` to scroll to the bottom after a new message is appended. Long conversations require the user to scroll manually.

**9. `createId` is exported but unused**

`frontend/src/lib/kanban.ts:164`

`createId` was used when card IDs were generated client-side. IDs are now generated server-side; this export is dead code.

**10. Message keys in `AiChatSidebar` use array index**

`frontend/src/components/AiChatSidebar.tsx:67`

```tsx
key={`${message.role}-${index}`}
```

`role` is only `"user"` or `"assistant"`, so consecutive messages from the same role share a key prefix that differs only by index. If history is ever trimmed or reordered, React will reconcile incorrectly. Use a stable unique key (e.g. a monotonic counter attached when the message is created).

---

### Infrastructure

**11. SQLite database is not persisted across container rebuilds**

`docker-compose.yml`

The database lives at `backend/app/data/pm.db` inside the container image layer. `docker compose up --build` destroys all board data on every rebuild. Add a named volume:

```yaml
services:
  backend:
    volumes:
      - pm_data:/app/app/data

volumes:
  pm_data:
```

**12. No `.dockerignore`**

The Docker build context includes `node_modules`, `.git`, test results, and the frontend dev cache. Add a `.dockerignore` to speed up builds and reduce image size:

```
.git
frontend/node_modules
frontend/.next
frontend/test-results
backend/app/data
```

**13. Playwright e2e tests cannot run in dev mode**

`frontend/playwright.config.ts`

The Playwright config starts `npm run dev` (Next.js dev server, port 3000). API calls from the browser go to `http://127.0.0.1:3000/api/...`, but the FastAPI backend is on port 8000. Because the project uses Next.js static export (`output: "export"`), `rewrites()` are not supported, so there is no built-in proxy.

The e2e tests must run against the compiled backend (which serves both the frontend and the API on the same port). The Playwright config should be updated to point at port 8000 and start the backend, not the dev server. Until then, e2e tests only pass if the backend is manually started on port 3000 before running Playwright.

---

## Missing test coverage

| Gap | Priority |
|---|---|
| `create_card` position-0 bug (item 1 above) | High — can be reproduced with a simple pytest |
| Cross-column `move_card` with an empty target column | Medium |
| `update_card` with empty title/details | Low |
| AI chat sidebar UI (messages render, send, error state) | Medium — Part 10 plan checklist item |
| E2e test for chat-driven card change | Medium — Part 10 plan checklist item |
| E2e test for column rename | Low |
