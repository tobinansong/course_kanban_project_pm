# Database approach

## Goals

- Normalize core entities: users, boards, columns, cards.
- Preserve ordering for columns and cards with explicit positions.
- Keep writes simple and deterministic for the MVP.

## Schema overview

The schema is defined in docs/database-schema.json and targets SQLite.

- users: account identity, even though the MVP only supports one login.
- boards: one board per user for the MVP, expandable later.
- columns: ordered by position within a board.
- cards: ordered by position within a column.

## Ordering strategy

- columns.position is unique per board.
- cards.position is unique per column.
- Move operations update positions in a single transaction.

## IDs

- Use text IDs to stay consistent across client and server.
- IDs are generated server-side in later parts.

## Migrations

- For the MVP, schema creation runs at startup if tables are missing.
- The schema version is stored in code, not the database.
- If changes are required, new SQL migrations will be added with explicit version bumps.

## Sample data

Seed data in docs/database-schema.json mirrors the current frontend demo board to ease initial integration.
