import asyncio
import json
from pathlib import Path

from .rules import InvalidTransition, apply_transition
from .schemas import Action, ReviewItem


class NotFound(Exception):
    def __init__(self, item_id: str):
        self.item_id = item_id
        super().__init__(f"Item {item_id} not found")


class Store:
    """In-memory item store with an atomic transition primitive.

    The lock, lookup, rule application, and write-back live behind one
    method so callers cannot accidentally interleave a read with a
    concurrent transition.
    """

    def __init__(self) -> None:
        self._items: dict[str, ReviewItem] = {}
        self._lock = asyncio.Lock()

    def load_seed(self, path: Path) -> None:
        raw = json.loads(path.read_text())
        self._items = {
            entry["id"]: ReviewItem.model_validate(entry) for entry in raw
        }

    def get_all(self) -> list[ReviewItem]:
        return list(self._items.values())

    def get(self, item_id: str) -> ReviewItem:
        item = self._items.get(item_id)
        if item is None:
            raise NotFound(item_id)
        return item

    async def transition(
        self, item_id: str, action: Action, reviewer: str
    ) -> ReviewItem:
        async with self._lock:
            item = self.get(item_id)
            updated = apply_transition(item, action, reviewer)
            self._items[updated.id] = updated
            return updated


store = Store()
