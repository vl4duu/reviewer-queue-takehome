<script setup lang="ts">
import type { QueueView } from "../api";
import type { ReviewItem } from "../types";
import QueueItem from "./QueueItem.vue";

const TERMINAL = new Set(["approved", "rejected", "escalated"]);

defineProps<{
  items: ReviewItem[];
  selectedId: string | null;
  view: QueueView;
}>();

defineEmits<{
  (e: "select", id: string): void;
  (e: "view-change", view: QueueView): void;
}>();

function isTerminal(status: string): boolean {
  return TERMINAL.has(status);
}
</script>

<template>
  <aside class="queue">
    <header class="queue-head">
      <h2>{{ view === "active" ? "Active queue" : "All items" }}</h2>
      <span class="count">{{ items.length }}</span>
    </header>

    <div class="toggle" role="tablist" aria-label="Queue view">
      <button
        type="button"
        role="tab"
        :aria-selected="view === 'active'"
        :class="{ active: view === 'active' }"
        @click="$emit('view-change', 'active')"
      >
        Active
      </button>
      <button
        type="button"
        role="tab"
        :aria-selected="view === 'all'"
        :class="{ active: view === 'all' }"
        @click="$emit('view-change', 'all')"
      >
        All
      </button>
    </div>

    <p v-if="items.length === 0" class="empty">
      {{ view === "active" ? "Queue is clear. Nothing to review." : "No items." }}
    </p>
    <ul v-else>
      <li v-for="(item, idx) in items" :key="item.id" :class="{ dimmed: isTerminal(item.status) }">
        <QueueItem
          :item="item"
          :selected="item.id === selectedId"
          :is-top="view === 'active' && idx === 0"
          @select="(id) => $emit('select', id)"
        />
      </li>
    </ul>
  </aside>
</template>

<style scoped>
.queue { display: flex; flex-direction: column; gap: var(--space-3); }
.queue-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
}
h2 { margin: 0; font-size: 16px; }
.count {
  background: var(--border);
  color: var(--text-muted);
  border-radius: 999px;
  padding: 2px 10px;
  font-size: 12px;
  font-weight: 600;
}
.toggle {
  display: inline-flex;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 2px;
  width: fit-content;
}
.toggle button {
  border: none;
  background: transparent;
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-muted);
}
.toggle button.active {
  background: var(--text);
  color: white;
}
ul { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: var(--space-2); }
li.dimmed { opacity: 0.6; }
.empty { color: var(--text-muted); font-style: italic; }
</style>
