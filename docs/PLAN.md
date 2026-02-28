# Project plan

This plan breaks work into numbered parts with clear checklists, tests, and success criteria. Each part should be completed and verified before moving on.

## Part 1: Plan

Checklist
- [ ] Expand this plan with concrete steps, tests, and success criteria for each part.
- [ ] Create frontend/AGENTS.md describing the existing frontend codebase (no code changes).
- [ ] Confirm plan scope and sequencing with the user before proceeding.
- [ ] Target ~80% unit test coverage when it is sensible; prioritize valuable tests over hitting a numeric threshold.
- [ ] Require robust integration testing for backend routes and frontend-to-backend flows.

Tests
- Documentation-only; no runtime tests.

Success criteria
- [ ] Plan is explicit and actionable.
- [ ] frontend/AGENTS.md exists and accurately reflects the frontend implementation.
- [ ] User approves the plan.

## Part 2: Scaffolding

Checklist
- [ ] Add Docker infrastructure to run backend and serve static content.
- [ ] Create FastAPI app in backend/ with a simple root HTML page and a JSON health endpoint.
- [ ] Configure Python deps using uv inside Docker.
- [ ] Add start/stop scripts for Mac, Windows, Linux in scripts/.
- [ ] Ensure a local run path works without Docker for faster iteration.

Tests
- [ ] `GET /` returns hello world HTML.
- [ ] `GET /api/health` returns JSON with status.
- [ ] Start/stop scripts run without errors on their target OS.

Success criteria
- [ ] Docker build and run succeeds.
- [ ] Backend responds to HTML and API requests.
- [ ] Scripts reliably start and stop the server.

## Part 3: Add frontend

Checklist
- [ ] Build the Next app for static output.
- [ ] Serve the built frontend from FastAPI at `/`.
- [ ] Ensure asset paths work under the same origin.
- [ ] Preserve existing UI look and behavior.

Tests
- [ ] Frontend unit tests (`npm run test:unit`) with sensible coverage targets focused on value.
- [ ] Frontend e2e tests (`npm run test:e2e`).
- [ ] Manual smoke: `/` renders the Kanban board in Docker.

Success criteria
- [ ] Kanban board UI is served at `/` via the backend.
- [ ] Unit and e2e tests pass.

## Part 4: Fake user sign-in

Checklist
- [ ] Add a simple login screen that gates access to the board.
- [ ] Accept only `user` / `password` and provide logout.
- [ ] Persist login state across refresh (cookie or local storage).
- [ ] Add backend endpoint to validate login if needed.

Tests
- [ ] Unit tests for login logic and UI gating with sensible coverage targets focused on value.
- [ ] E2e tests for login/logout flow.

Success criteria
- [ ] Unauthenticated users see only the login screen.
- [ ] Authenticated users see the Kanban board until logout.

## Part 5: Database modeling

Checklist
- [ ] Propose a normalized schema for users, boards, columns, and cards.
- [ ] Save schema as JSON in docs/ (include sample data).
- [ ] Document database approach and migration strategy.
- [ ] Get user sign-off before implementation.

Tests
- [ ] JSON schema file validates (basic structure and required fields).

Success criteria
- [ ] Schema is clear and approved.
- [ ] Docs explain how data is stored and related.

## Part 6: Backend

Checklist
- [ ] Implement SQLite data access and initialize DB if missing.
- [ ] Add API routes for board read/update, column rename, card CRUD, card move.
- [ ] Add request/response validation.
- [ ] Provide deterministic seed data for the single user.

Tests
- [ ] Backend unit tests for each route and data operation with sensible coverage targets focused on value.
- [ ] DB creation on first run is verified.

Success criteria
- [ ] API supports full Kanban CRUD for the user.
- [ ] Tests confirm data persistence and correct ordering.

## Part 7: Frontend + backend

Checklist
- [ ] Replace in-memory board state with API-backed state.
- [ ] Add optimistic UI updates with rollback on failure.
- [ ] Handle loading and error states.
- [ ] Ensure board refreshes after backend updates.

Tests
- [ ] Integration tests for API calls and UI sync (robust coverage of success and failure cases).
- [ ] E2e tests for core flows (move, add, rename, delete).

Success criteria
- [ ] Kanban changes persist across refresh.
- [ ] UI stays in sync with backend state.

## Part 8: AI connectivity

Checklist
- [ ] Add OpenRouter client using env key.
- [ ] Create a backend endpoint to run a simple prompt.
- [ ] Add minimal logging for request/response timing.

Tests
- [ ] Backend unit test for a basic `2+2` prompt with sensible coverage targets focused on value.
- [ ] Verify correct model configuration.

Success criteria
- [ ] AI call succeeds and returns expected content.

## Part 9: AI structured outputs

Checklist
- [ ] Define JSON schema for AI responses (message + optional board ops).
- [ ] Send board JSON plus conversation history to the model.
- [ ] Validate and apply board updates returned by the model.
- [ ] Log structured output validation failures.

Tests
- [ ] Unit tests for schema validation with sensible coverage targets focused on value.
- [ ] Integration tests for applying AI-driven updates (success and validation-failure paths).

Success criteria
- [ ] AI responses are parsed reliably.
- [ ] Board updates are applied safely and deterministically.

## Part 10: AI sidebar

Checklist
- [ ] Add a sidebar chat UI with history.
- [ ] Send user messages to the backend AI endpoint.
- [ ] Apply AI-driven board updates and refresh UI.
- [ ] Handle streaming or loading states gracefully.

Tests
- [ ] UI tests for chat message flow and board updates with sensible coverage targets focused on value.
- [ ] E2e test covering chat-driven card change.

Success criteria
- [ ] Sidebar chat works end-to-end.
- [ ] Board updates appear immediately after AI response.