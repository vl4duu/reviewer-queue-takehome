# Notes

## Stack

- Backend: FastAPI + Pydantic v2, in-memory store guarded by an `asyncio.Lock`. Seed loaded once at startup from `data/review_items.json`.
- Frontend: Vue 3 (`<script setup>`) + Vite + TypeScript. Plain scoped CSS with a token file. No router, no UI library.
- Tests: pytest + `TestClient` cover the rules + queue order matrix.

## Assumptions

- The spec mentions a `priority` field for queue ordering; the seed uses `customer_tier`. Ordered by `customer_tier` per CLAUDE.md.
- Current reviewer is hardcoded to `alex` (server-side constant + frontend constant).
- All state is in-process. Restarting the backend resets the seed; mutations are not written back to JSON.
- Risk levels and tiers are limited to the values present in the seed; Pydantic enforces them.

## Tradeoffs

- **Single transition endpoint** (`POST /api/items/{id}/transition` with an `action` body) instead of four named routes. Keeps the rules in one place and lets the frontend reuse one client function. Trades REST conventionality for clarity.
- **Server stays liberal on assignment.** Any caller can approve/reject/escalate any `in_review` item; the UI hides/disables the buttons when the assignee is someone other than `alex`. A real system would enforce assignee match server-side. Called out in `rules.py`.
- **No optimistic UI / no confirm dialog on terminal actions.** After a successful action the queue is refetched; if the item dropped from the active list, a banner surfaces the new terminal status. Simpler than reconciling local state and avoids the case where the client and server diverge.
- **Plain scoped CSS, no UI kit.** Saves install/setup time at the cost of generic visuals. A small token file (`assets/base.css`) keeps risk/status colors consistent.
- **Test coverage.** Backend rules + queue order live in 9 pytest cases against the HTTP layer; the `Store.transition` primitive has 3 direct async tests. Frontend has 6 vitest cases on the action-availability policy (`src/policy.ts`).
- **Two-process dev model.** Vite proxies `/api` → `http://localhost:8000`; no CORS code, no bundling of the backend.

## Architecture choices worth flagging

- **`Store.transition(item_id, action, reviewer)` owns the lock.** The atomic sequence (lookup → apply rules → write back) is one method, so the FastAPI handler only translates `NotFound` / `InvalidTransition` into HTTP status codes. The same primitive could back a CLI or batch processor without re-implementing the locking discipline.
- **`src/policy.ts :: availableActions(item, currentUser)` is a pure function.** `ActionBar.vue` is a renderer over its return value (`available`, `disabledReason`, `terminalMessage`). The visibility matrix has a name, a single home, and a unit test surface — no template branches encode policy.

## What I'd add with more time

- Server-side enforcement of `assigned_reviewer == current_user` for approve/reject/escalate.
- Confirm step on terminal actions (irreversible from the UI).
- A vitest smoke test mounting `App.vue` with `fetch` mocked.
- Component tests for `ActionBar`'s visibility matrix (status × assignment).
- Persist transitions to SQLite as an audit log; expose a `GET /api/items/{id}/history`.
- Notes pane (seed has `notes_count` but no notes content — would need new seed data).
- WebSocket or SSE push so multiple reviewers see queue updates without polling.

### If this grew up to need real persistence + concurrency

I walked through the design separately. Sketch, not a commitment for this submission:

- **Motivation drives the schema.** The two real reasons to reach for a DB here are an audit log (regulators / ops want "who did what when") and true multi-reviewer concurrency (today's `asyncio.Lock` only protects within one process). Persistence and multi-instance ops fall out for free once those two are solved.
- **Schema: snapshot + append-only log.** A `review_items` table holds current state (one row per item, mutated in place); a `transitions` table is append-only `(id, item_id, actor, action, from_status, to_status, occurred_at)`. Both rows written in one transaction. Pure event-sourcing is overkill for four actions and one terminal flag.
- **Access layer: asyncpg + raw SQL.** The query surface is tiny (~5 statements). SQLAlchemy's unit-of-work model fights the locking-then-mutating pattern; Pydantic already covers validation. Migrations as numbered `.sql` files run by `yoyo-migrations` or a startup script.
- **Concurrency: drop the asyncio lock, use `SELECT … FOR UPDATE`.** Inside the transition transaction, lock the `review_items` row, re-read status, apply rules in Python, write the snapshot update + transitions insert, commit. This is also where the server finally enforces `assigned_reviewer == current_user` — the gap currently papered over by the UI.
- **Keep the `Store` seam, don't burn it.** I initially talked myself into inlining DB calls into the route handlers. On reflection that's the wrong call: `InMemoryStore` is too valuable as a fast test fixture, and the existing test suite already proves the seam carries its weight. Add `PostgresStore` as a second adapter; keep `InMemoryStore` for unit tests; reserve testcontainers for the integration tests that exercise locking + transactional audit-write behaviour.
- **Interface evolution.** Replace `get_all()` with `active_queue() -> list[ReviewItem]` (terminals excluded, ordered) so the queue rules push into SQL rather than sorting 50k items in Python. Drop `load_seed` from the interface — production seeding becomes a data migration, not a runtime method.

## Out of scope (per spec)

Auth, deployment, containerization, background jobs, multi-user concurrency beyond the in-process lock, polished visuals, frontend routing.
