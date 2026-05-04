<script setup lang="ts">
import type { ReviewItem } from "../types";

defineProps<{
  item: ReviewItem;
  selected: boolean;
  isTop: boolean;
}>();

defineEmits<{ (e: "select", id: string): void }>();

function relativeTime(iso: string): string {
  const then = new Date(iso).getTime();
  const diffMs = Date.now() - then;
  const mins = Math.round(diffMs / 60000);
  const rtf = new Intl.RelativeTimeFormat("en", { numeric: "auto" });
  if (Math.abs(mins) < 60) return rtf.format(-mins, "minute");
  const hours = Math.round(mins / 60);
  if (Math.abs(hours) < 48) return rtf.format(-hours, "hour");
  const days = Math.round(hours / 24);
  return rtf.format(-days, "day");
}
</script>

<template>
  <button
    type="button"
    class="row"
    :class="{ selected }"
    :style="{ borderLeftColor: `var(--risk-${item.risk_level})` }"
    @click="$emit('select', item.id)"
  >
    <div class="row-top">
      <span class="title">{{ item.title }}</span>
      <span v-if="item.customer_tier === 'priority'" class="tier">PRIORITY</span>
    </div>
    <div class="row-meta">
      <span class="badge" :style="{ background: `var(--status-${item.status})` }">
        {{ item.status }}
      </span>
      <span class="risk">{{ item.risk_level }} risk</span>
      <span class="dot">·</span>
      <span>{{ relativeTime(item.submitted_at) }}</span>
      <span class="dot">·</span>
      <span>{{ item.notes_count }} notes</span>
      <span v-if="isTop" class="top-tag">Top of queue</span>
    </div>
  </button>
</template>

<style scoped>
.row {
  width: 100%;
  text-align: left;
  background: var(--surface);
  border: 1px solid var(--border);
  border-left-width: 4px;
  border-radius: var(--radius);
  padding: var(--space-3);
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}
.row:hover { background: #fafbfd; }
.row.selected { box-shadow: var(--focus); border-color: #2563eb; }
.row-top { display: flex; justify-content: space-between; align-items: center; gap: var(--space-2); }
.title { font-weight: 600; }
.tier {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.04em;
  background: var(--tier-priority);
  color: white;
  padding: 2px 6px;
  border-radius: 4px;
}
.row-meta {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: 12px;
  color: var(--text-muted);
  flex-wrap: wrap;
}
.risk { text-transform: capitalize; }
.dot { color: var(--border); }
.top-tag {
  margin-left: auto;
  font-size: 11px;
  font-weight: 600;
  color: var(--risk-high);
}
</style>
