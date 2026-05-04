import type { Action, ReviewItem } from "./types";

const base = "/api";

export type QueueView = "active" | "all";

export class TransitionError extends Error {}

async function parseOrThrow(res: Response): Promise<any> {
  if (res.ok) return res.json();
  let detail = `${res.status} ${res.statusText}`;
  try {
    const body = await res.json();
    if (body?.detail) detail = body.detail;
  } catch {
    /* ignore */
  }
  throw new TransitionError(detail);
}

export async function fetchQueue(view: QueueView = "active"): Promise<ReviewItem[]> {
  const res = await fetch(`${base}/items?include=${view}`);
  return parseOrThrow(res);
}

export async function transition(id: string, action: Action): Promise<ReviewItem> {
  const res = await fetch(`${base}/items/${id}/transition`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action }),
  });
  return parseOrThrow(res);
}
