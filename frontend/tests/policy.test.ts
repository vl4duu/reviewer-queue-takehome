import { describe, expect, it } from "vitest";
import { availableActions } from "../src/policy";
import type { ReviewItem, Status } from "../src/types";

function item(overrides: Partial<ReviewItem> = {}): ReviewItem {
  return {
    id: "RV-1",
    title: "x",
    submitted_at: "2026-04-01T00:00:00Z",
    risk_level: "high",
    customer_tier: "priority",
    status: "unassigned",
    assigned_reviewer: null,
    notes_count: 0,
    summary: "x",
    ...overrides,
  };
}

describe("availableActions", () => {
  it("offers claim on unassigned", () => {
    const p = availableActions(item({ status: "unassigned" }), "alex");
    expect(p.available).toEqual(["claim"]);
    expect(p.disabledReason).toBeNull();
    expect(p.terminalMessage).toBeNull();
  });

  it("offers approve/reject/escalate when item is mine", () => {
    const p = availableActions(
      item({ status: "in_review", assigned_reviewer: "alex" }),
      "alex",
    );
    expect(p.available).toEqual(["approve", "reject", "escalate"]);
    expect(p.disabledReason).toBeNull();
  });

  it("blocks terminal actions when assigned to someone else", () => {
    const p = availableActions(
      item({ status: "in_review", assigned_reviewer: "sam" }),
      "alex",
    );
    expect(p.available).toEqual([]);
    expect(p.disabledReason).toContain("sam");
  });

  it.each<Status>(["approved", "rejected", "escalated"])(
    "returns terminal message for %s",
    (status) => {
      const p = availableActions(item({ status }), "alex");
      expect(p.available).toEqual([]);
      expect(p.terminalMessage).toContain(status);
    },
  );
});
