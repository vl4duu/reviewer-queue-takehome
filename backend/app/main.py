from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Query

from .rules import CURRENT_REVIEWER, InvalidTransition, active_queue, full_queue
from .schemas import ReviewItem, TransitionRequest
from .store import NotFound, store

SEED_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "review_items.json"


@asynccontextmanager
async def lifespan(_: FastAPI):
    store.load_seed(SEED_PATH)
    yield


app = FastAPI(title="Reviewer Queue", lifespan=lifespan)


@app.get("/api/items", response_model=list[ReviewItem])
async def list_items(
    include: Literal["active", "all"] = Query("active"),
) -> list[ReviewItem]:
    items = store.get_all()
    return full_queue(items) if include == "all" else active_queue(items)


@app.get("/api/items/{item_id}", response_model=ReviewItem)
async def get_item(item_id: str) -> ReviewItem:
    try:
        return store.get(item_id)
    except NotFound as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/api/items/{item_id}/transition", response_model=ReviewItem)
async def transition_item(item_id: str, req: TransitionRequest) -> ReviewItem:
    try:
        return await store.transition(item_id, req.action, CURRENT_REVIEWER)
    except NotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidTransition as e:
        raise HTTPException(status_code=409, detail=str(e))
