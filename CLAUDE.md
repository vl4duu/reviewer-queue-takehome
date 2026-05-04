# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository status

This is a take-home exercise scaffold. At baseline, the repo contains **only** the spec (`README.md`), seed data (`data/review_items.json`), and a field reference (`examples/seed_preview.md`). No backend, frontend, build system, package manifest, or tests exist yet — choose the stack and structure when implementing.

The task is timeboxed (~60 min, hard stop 90 min). Prioritize one working flow + correct rules + usable UI over polish. Persistence beyond process lifetime is not required; in-memory state is acceptable.

## Domain: reviewer queue

Operations reviewers triage submissions through a fixed state machine. Implementations must enforce these rules — they are the primary evaluation criterion.

### State machine

- States: `unassigned`, `in_review`, `approved`, `rejected`, `escalated`.
- Terminal: `approved`, `rejected`, `escalated`. No further actions allowed once terminal.
- Transitions:
  - `claim`: only from `unassigned` → `in_review`. Must record the acting reviewer on `assigned_reviewer`.
  - `approve` / `reject` / `escalate`: only from `in_review` → terminal.
- Invalid actions must be rejected cleanly (don't silently no-op).
- Current reviewer identity may be hardcoded (e.g. `alex`).

### Active queue

Active queue **excludes** terminal items. Order by urgency, in this exact precedence:

1. `risk_level`: `high` > `medium` > `low`
2. tiebreak: `customer_tier` `priority` > `standard`
3. tiebreak: older `submitted_at` first

### Seed data shape

`data/review_items.json` — array of items with: `id`, `title`, `submitted_at` (ISO-8601 UTC), `risk_level` (`high|medium|low`), `customer_tier` (`priority|standard`), `status`, `assigned_reviewer` (nullable), `notes_count` (int), `summary`. See `examples/seed_preview.md` for sample records and field notes.

Note: the spec mentions a `priority` field for queue ordering but the seed data uses `customer_tier` — order by `customer_tier` (this is what the seed supports).

## Deliverables

Submission expects: GitHub repo, `NOTES.md` (assumptions, tradeoffs, next steps), and a ~3-min walkthrough. Keep `NOTES.md` in sync when implementation decisions change.

## Out of scope

Auth, deployment, containerization, background jobs, multi-user concurrency, pixel-perfect styling. Don't build these unless explicitly asked.