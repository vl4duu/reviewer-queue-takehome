import type { Action, ReviewItem } from "./types";

const TERMINAL = new Set(["approved", "rejected", "escalated"]);

export interface ActionAvailability {
  available: Action[];
  disabledReason: string | null;
  terminalMessage: string | null;
}

/**
 * Pure projection from (item, currentUser) to what the reviewer is allowed
 * to do right now. The renderer (ActionBar) only consumes this.
 */
export function availableActions(
  item: ReviewItem,
  currentUser: string,
): ActionAvailability {
  if (TERMINAL.has(item.status)) {
    return {
      available: [],
      disabledReason: null,
      terminalMessage: `Item is ${item.status}. No further actions.`,
    };
  }

  if (item.status === "unassigned") {
    return { available: ["claim"], disabledReason: null, terminalMessage: null };
  }

  // in_review
  const isMine = item.assigned_reviewer === currentUser;
  return {
    available: isMine ? ["approve", "reject", "escalate"] : [],
    disabledReason: isMine
      ? null
      : `Assigned to ${item.assigned_reviewer ?? "another reviewer"}`,
    terminalMessage: null,
  };
}
