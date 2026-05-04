from .schemas import Action, ReviewItem

RISK_RANK = {"high": 0, "medium": 1, "low": 2}
TIER_RANK = {"priority": 0, "standard": 1}
TERMINAL = {"approved", "rejected", "escalated"}
CURRENT_REVIEWER = "alex"


class InvalidTransition(Exception):
    def __init__(self, status: str, action: str):
        self.status = status
        self.action = action
        super().__init__(f"Cannot {action} item in status {status}")


def _urgency_key(item: ReviewItem) -> tuple[int, int, object]:
    return (
        RISK_RANK[item.risk_level],
        TIER_RANK[item.customer_tier],
        item.submitted_at,
    )


def active_queue(items: list[ReviewItem]) -> list[ReviewItem]:
    return sorted((i for i in items if i.status not in TERMINAL), key=_urgency_key)


def full_queue(items: list[ReviewItem]) -> list[ReviewItem]:
    """Active items first (sorted by urgency), then terminals (most recent first).

    Terminals sit at the bottom so the reviewer's primary work surface stays
    on top, while still letting them inspect what was already resolved.
    """
    active = [i for i in items if i.status not in TERMINAL]
    terminal = [i for i in items if i.status in TERMINAL]
    return sorted(active, key=_urgency_key) + sorted(
        terminal, key=lambda i: i.submitted_at, reverse=True
    )


def apply_transition(item: ReviewItem, action: Action, reviewer: str) -> ReviewItem:
    if action == "claim":
        if item.status != "unassigned":
            raise InvalidTransition(item.status, action)
        return item.model_copy(update={"status": "in_review", "assigned_reviewer": reviewer})

    # approve / reject / escalate
    if item.status != "in_review":
        raise InvalidTransition(item.status, action)
    terminal_status = {"approve": "approved", "reject": "rejected", "escalate": "escalated"}[action]
    return item.model_copy(update={"status": terminal_status})
