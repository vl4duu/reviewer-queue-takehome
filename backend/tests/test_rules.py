from app.rules import RISK_RANK, TIER_RANK


TERMINAL = {"approved", "rejected", "escalated"}


def test_list_excludes_terminal_items(client):
    res = client.get("/api/items")
    assert res.status_code == 200
    statuses = {i["status"] for i in res.json()}
    assert statuses.isdisjoint(TERMINAL)


def test_queue_ordered_by_risk(client):
    items = client.get("/api/items").json()
    risks = [RISK_RANK[i["risk_level"]] for i in items]
    assert risks == sorted(risks)


def test_queue_tiebreak_priority_over_standard(client):
    items = client.get("/api/items").json()
    high = [i for i in items if i["risk_level"] == "high"]
    tiers = [TIER_RANK[i["customer_tier"]] for i in high]
    assert tiers == sorted(tiers)


def test_queue_tiebreak_older_first(client):
    items = client.get("/api/items").json()
    # Within same (risk, tier) bucket, submitted_at must be ascending.
    buckets: dict[tuple[str, str], list[str]] = {}
    for i in items:
        buckets.setdefault((i["risk_level"], i["customer_tier"]), []).append(i["submitted_at"])
    for stamps in buckets.values():
        assert stamps == sorted(stamps)


def test_claim_unassigned_moves_to_in_review(client):
    res = client.post("/api/items/RV-1024/transition", json={"action": "claim"})
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "in_review"
    assert body["assigned_reviewer"] == "alex"


def test_claim_in_review_rejected(client):
    res = client.post("/api/items/RV-1027/transition", json={"action": "claim"})
    assert res.status_code == 409


def test_terminal_actions_from_in_review(client):
    for item_id, action, terminal in [
        ("RV-1027", "approve", "approved"),
        ("RV-1028", "reject", "rejected"),
        ("RV-1030", "escalate", "escalated"),
    ]:
        res = client.post(f"/api/items/{item_id}/transition", json={"action": action})
        assert res.status_code == 200, res.text
        assert res.json()["status"] == terminal


def test_action_on_terminal_rejected(client):
    # RV-1029 is approved in seed.
    for action in ["claim", "approve", "reject", "escalate"]:
        res = client.post("/api/items/RV-1029/transition", json={"action": action})
        assert res.status_code == 409


def test_unknown_item_404(client):
    res = client.post("/api/items/RV-9999/transition", json={"action": "claim"})
    assert res.status_code == 404


def test_include_all_returns_terminals_at_end(client):
    items = client.get("/api/items?include=all").json()
    assert len(items) == 12
    statuses = [i["status"] for i in items]
    last_active = max(
        idx for idx, s in enumerate(statuses) if s not in TERMINAL
    )
    first_terminal = min(
        (idx for idx, s in enumerate(statuses) if s in TERMINAL), default=len(statuses)
    )
    assert last_active < first_terminal
