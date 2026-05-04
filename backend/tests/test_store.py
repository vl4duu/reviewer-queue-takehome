import pytest

from app.rules import InvalidTransition
from app.store import NotFound


@pytest.mark.asyncio
async def test_transition_returns_updated_item(fresh_store):
    updated = await fresh_store.transition("RV-1024", "claim", "alex")
    assert updated.status == "in_review"
    assert updated.assigned_reviewer == "alex"
    assert fresh_store.get("RV-1024").status == "in_review"


@pytest.mark.asyncio
async def test_transition_unknown_id_raises_not_found(fresh_store):
    with pytest.raises(NotFound):
        await fresh_store.transition("RV-9999", "claim", "alex")


@pytest.mark.asyncio
async def test_transition_invalid_action_raises_and_does_not_mutate(fresh_store):
    before = fresh_store.get("RV-1029")  # already approved
    with pytest.raises(InvalidTransition):
        await fresh_store.transition("RV-1029", "approve", "alex")
    after = fresh_store.get("RV-1029")
    assert before == after
