# Frontend codebase notes

## Overview

The frontend is a Next.js 16 app using the App Router. It renders a single-page Kanban board with in-memory state and drag-and-drop interactions. There is no backend integration yet; all data is local to the browser session.

## Structure

- src/app/layout.tsx: Root layout, font setup, and metadata.
- src/app/page.tsx: Renders the Kanban board.
- src/app/globals.css: Global styles and CSS variables for the color system.
- src/components/: UI components for the board, columns, cards, and add-card form.
- src/lib/kanban.ts: In-memory data model, seed data, and card move logic.
- src/lib/kanban.test.ts: Unit tests for move logic.
- src/components/KanbanBoard.test.tsx: UI tests for rename, add, and delete.

## Data model and state

- Board state is kept in React state within KanbanBoard.
- Columns are fixed in the seed data but titles are editable.
- Cards are stored in a map keyed by id; columns contain ordered card id lists.
- New card ids are generated client-side with a random plus timestamp suffix.

## UI behavior

- Drag and drop uses @dnd-kit with pointer sensors and a drag overlay.
- Columns are droppable targets; cards are sortable within a column.
- Deleting a card removes it from both the card map and the column list.

## Tests

- Unit tests: vitest + testing-library for board interactions.
- Library tests: vitest for card move logic.
- E2e tests: Playwright config exists for full UI flows.

## Tooling

- Scripts in package.json support dev, build, start, lint, and tests.
- Tailwind CSS v4 is configured via postcss.
