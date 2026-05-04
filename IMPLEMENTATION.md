# Implementation Plan

Concrete plan for the reviewer queue take-home. Decisions locked during the design pass; this doc is the source of truth for execution.

## 1. Stack

- **Backend:** FastAPI + uvicorn. In-memory state (module-level dict). `asyncio.Lock` around the transition handler.
- **Frontend:** Vite + Vue 3 (`<script setup>` SFCs). Plain scoped CSS per component + one shared tokens file. No UI library, no Tailwind, no router.
- **Tests:** pytest + `httpx.AsyncClient`/`TestClient` for backend (rules + queue order). vitest + `@vue/test-utils` for one frontend smoke test.
- **Dev:** two terminals. Vite proxies `/api` → `http://localhost:8000`. No CORS code.

## 2. Repo layout

```
.
├── README.md                 # existing
├── NOTES.md                  # new — assumptions, tradeoffs, next steps
├── data/review_items.json    # existing
├── examples/seed_preview.md  # existing
├── backend/
│   ├── requirements.txt      # fastapi, uvicorn, pytest, httpx
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py           # FastAPI app, routes
│   │   ├── store.py          # in-memory dict, lock, seed loader
│   │   ├── rules.py          # state machine, queue ordering
│   │   └── schemas.py        # pydantic models
│   └── tests/
│       ├── conftest.py
│       └── test_rules.py
└── frontend/
    ├── package.json
    ├── vite.config.ts
    ├── index.html
    ├── src/
    │   ├── main.ts
    │   ├── App.vue
    │   ├── api.ts            # fetchQueue, fetchItem, transition
    │   ├── assets/base.css   # reset + color tokens
    │   └── components/
    │       ├── QueueList.vue
    │       ├── QueueItem.vue
    │       ├── DetailPanel.vue
    │       └── ActionBar.vue
    └── tests/
        └── App.smoke.test.ts
```

## 3. Backend design

### 3.1 Domain model (`schemas.py`)

```python
class ReviewItem(BaseModel):
    id: str
    title: str
    submitted_at: datetime
    risk_level: Literal["high", "medium", "low"]
    customer_tier: Literal["priority", "standard"]
    status: Literal["unassigned", "in_review", "approved", "rejected", "escalated"]
    assigned_reviewer: str | None
    notes_count: int
    summary: str

class TransitionRequest(BaseModel):
    action: Literal["claim", "approve", "reject", "escalate"]
```

### 3.2 Store (`store.py`)

- Module-level `_items: dict[str, ReviewItem] = {}`.
- Module-level `_lock = asyncio.Lock()`.
- `load_seed(path: Path) -> None`: read JSON, parse into `ReviewItem`, populate dict. Called once at app startup.
- `get_all() -> list[ReviewItem]`: returns deep copies (or rely on Pydantic immutability — `model_copy()`).
- `get(id) -> ReviewItem | None`.
- `replace(item: ReviewItem) -> None`: writes back into dict (called inside `_lock`).
- `lock()` exposed for the transition handler.

No file writes. Mutations live and die in the process.

### 3.3 Rules (`rules.py`)

```python
RISK_RANK = {"high": 0, "medium": 1, "low": 2}
TIER_RANK = {"priority": 0, "standard": 1}
TERMINAL = {"approved", "rejected", "escalated"}
CURRENT_REVIEWER = "alex"

def active_queue(items: list[ReviewItem]) -> list[ReviewItem]:
    return sorted(
        (i for i in items if i.status not in TERMINAL),
        key=lambda i: (RISK_RANK[i.risk_level], TIER_RANK[i.customer_tier], i.submitted_at),
    )

def apply_transition(item: ReviewItem, action: str, reviewer: str) -> ReviewItem:
    # raises InvalidTransition on illegal action.
    # claim: unassigned -> in_review, sets assigned_reviewer=reviewer
    # approve/reject/escalate: in_review (any assignee) -> terminal
    # NOTE: "any assignee" decision — rules.py allows the transition; the UI is the
    # gate that hides/disables foreign-assignment actions. Server stays liberal for
    # simplicity; revisit in NOTES.md.
    ...

class InvalidTransition(Exception):
    def __init__(self, item_status: str, action: str): ...
```

### 3.4 API (`main.py`)

- `GET /api/items` → list of active queue items, sorted.
- `GET /api/items/all` → all items including terminal (used to render terminal item details if linked from elsewhere — optional, skip if tight on time).
- `GET /api/items/{id}` → single item or 404.
- `POST /api/items/{id}/transition` body `{action}` →
  - 200 with updated item on success
  - 404 if id unknown
  - 409 with `{detail: "Cannot <action> item in status <status>"}` on `InvalidTransition`

Transition handler skeleton:

```python
@app.post("/api/items/{item_id}/transition")
async def transition(item_id: str, req: TransitionRequest):
    async with store.lock():
        item = store.get(item_id)
        if item is None:
            raise HTTPException(404)
        try:
            updated = apply_transition(item, req.action, CURRENT_REVIEWER)
        except InvalidTransition as e:
            raise HTTPException(409, detail=str(e))
        store.replace(updated)
        return updated
```

Startup hook: `load_seed(Path(__file__).parent.parent.parent / "data/review_items.json")`.

## 4. Frontend design

### 4.1 Component tree

```
App.vue
├── QueueList.vue            # left column
│   └── QueueItem.vue (×N)   # one per item, click to select
└── DetailPanel.vue          # right column, shows selected item
    └── ActionBar.vue        # contextual buttons
```

### 4.2 State (in `App.vue`)

```ts
const items = ref<ReviewItem[]>([])
const selectedId = ref<string | null>(null)
const selected = computed(() => items.value.find(i => i.id === selectedId.value) ?? null)
const loading = ref(true)
const error = ref<string | null>(null)
const actionError = ref<string | null>(null)  // shown inline in DetailPanel
```

`refresh()` = `fetchQueue()`; called on mount and after every successful action. After action, `selectedId` retained; if the item went terminal it disappears from the queue, in which case the detail panel shows the last-known terminal state from the action's response (kept in `lastTerminal` ref) until selection cleared.

Simpler alternative considered: refetch list, then if selected item dropped from list, clear selection and surface a banner ("RV-1024 was approved"). **Pick this** — fewer edge cases.

### 4.3 Action visibility (in `ActionBar.vue`)

Props: `item: ReviewItem`, `currentUser: string`. Local `confirming = ref<string | null>(null)` unused (no confirm dialog).

| Status | assigned_reviewer | Buttons |
|---|---|---|
| `unassigned` | — | `Claim` |
| `in_review` | === alex | `Approve`, `Reject`, `Escalate` |
| `in_review` | !== alex | three buttons disabled, hint text "Assigned to {name}" |
| terminal | — | none, banner showing terminal status |

### 4.4 Queue UI (in `QueueItem.vue`)

- Left border 4px, color from `--risk-{level}` token.
- Title row: title + tier badge if `priority`.
- Meta row: status badge, relative timestamp (`Intl.RelativeTimeFormat`), notes count.
- First item additionally shows a small "Top of queue" tag.

### 4.5 Styling tokens (`assets/base.css`)

- `--risk-high`, `--risk-medium`, `--risk-low`
- `--tier-priority` accent
- `--status-unassigned`, `--status-in_review`, `--status-approved`, `--status-rejected`, `--status-escalated`
- spacing scale, font stack, focus ring

Layout: CSS grid, two columns at ≥768px, single column below.

### 4.6 API client (`api.ts`)

```ts
const base = "/api"
export async function fetchQueue(): Promise<ReviewItem[]>
export async function transition(id: string, action: Action): Promise<ReviewItem>
```

`transition` parses the 409 body and throws `new TransitionError(message)` so `App.vue` can surface `actionError`.

### 4.7 Vite proxy

```ts
// vite.config.ts
server: { proxy: { "/api": "http://localhost:8000" } }
```

## 5. Tests

### 5.1 Backend (`backend/tests/test_rules.py`)

`TestClient` against the FastAPI app. Each test resets the in-memory store via a fixture that re-runs `load_seed`.

Coverage matrix (≈8 tests):

1. `GET /api/items` excludes terminal items.
2. Queue order: `high > medium > low`.
3. Queue order tiebreak: same risk, `priority > standard`.
4. Queue order tiebreak: same risk + tier, older `submitted_at` first.
5. `claim` on `unassigned` → `in_review`, assigned_reviewer set to `alex`.
6. `claim` on `in_review` → 409.
7. `approve` / `reject` / `escalate` from `in_review` → terminal.
8. Any action on terminal → 409.

### 5.2 Frontend (`frontend/tests/App.smoke.test.ts`)

Mount `App.vue` with `fetch` mocked to return a fixture queue. Assert:

- Queue renders one row per item.
- Click first row → DetailPanel shows item title.
- Click `Claim` → mock POST resolves, list refetches with status `in_review`.

One test. Don't expand unless time permits.

## 6. Sequence (60-min budget, 90-min hard stop)

| Window | Goal | Done-when |
|---|---|---|
| 0–10 | FastAPI skeleton, seed loader, `GET /api/items` sorted active queue | curl returns sorted JSON, terminal items absent |
| 10–20 | Vite + Vue scaffold, `base.css` tokens, `QueueList` rendering live data | open browser, see ordered list with risk colors |
| 20–30 | `DetailPanel`, transition endpoint, `claim` working end-to-end | click Claim on RV-1024 → status flips, re-renders. **Hard checkpoint.** |
| 30–40 | Approve/Reject/Escalate, foreign-assignment disable, inline 409 error | every state transition demonstrable in UI |
| 40–50 | Backend pytest suite (8 tests) | `pytest` green |
| 50–55 | vitest smoke test | `npm test` green |
| 55–60 | README run instructions, NOTES.md draft | submission-ready |

Buffer 60–90: polish (focus styles, empty queue state, banner for terminal selection), record walkthrough.

**Cut order if behind:** vitest test → frontend polish → confirm/cancel UX nuances → README polish. Never cut backend tests; never cut the state-machine correctness.

## 7. NOTES.md content (draft outline)

- **Assumptions**
  - `customer_tier` interpreted as the spec's `priority` field for queue ordering.
  - Hardcoded reviewer = `alex`.
  - In-memory state; mutations don't write to `data/review_items.json`.
- **Tradeoffs**
  - Single transition endpoint over four named ones — rules consolidated in one place; trades REST conventionality for clarity.
  - No confirm dialog on terminal actions — deliberate scope cut for an internal tool. Easy to add back.
  - Server allows any reviewer to approve/reject/escalate any `in_review` item; UI is the only gate. Real system would enforce assignee match server-side.
  - Frontend test coverage is one smoke test — backend rules tests carry the correctness story.
  - Plain scoped CSS instead of a UI library — saves install/setup time at the cost of generic visuals.
- **Next with more time**
  - Server-side reviewer-match enforcement.
  - Confirm step on terminal actions.
  - Optimistic UI + reconciliation on error.
  - Persist transitions to SQLite for audit log.
  - Component tests for `ActionBar` visibility matrix.
  - Notes pane (seed has `notes_count` but no notes content — would need new data).

## 8. Explicitly out of scope

Auth, deployment, containerization, background jobs, multi-user concurrency beyond the in-process lock, polished visual design, frontend routing, optimistic updates, confirm dialogs.
