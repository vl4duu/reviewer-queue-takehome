export type RiskLevel = "high" | "medium" | "low";
export type CustomerTier = "priority" | "standard";
export type Status =
  | "unassigned"
  | "in_review"
  | "approved"
  | "rejected"
  | "escalated";
export type Action = "claim" | "approve" | "reject" | "escalate";

export interface ReviewItem {
  id: string;
  title: string;
  submitted_at: string;
  risk_level: RiskLevel;
  customer_tier: CustomerTier;
  status: Status;
  assigned_reviewer: string | null;
  notes_count: number;
  summary: string;
}
