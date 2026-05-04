from datetime import datetime
from typing import Literal

from pydantic import BaseModel

RiskLevel = Literal["high", "medium", "low"]
CustomerTier = Literal["priority", "standard"]
Status = Literal["unassigned", "in_review", "approved", "rejected", "escalated"]
Action = Literal["claim", "approve", "reject", "escalate"]


class ReviewItem(BaseModel):
    id: str
    title: str
    submitted_at: datetime
    risk_level: RiskLevel
    customer_tier: CustomerTier
    status: Status
    assigned_reviewer: str | None
    notes_count: int
    summary: str


class TransitionRequest(BaseModel):
    action: Action
