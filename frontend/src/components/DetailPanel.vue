<script setup lang="ts">
import type { Action, ReviewItem } from "../types";
import ActionBar from "./ActionBar.vue";

defineProps<{
  item: ReviewItem | null;
  currentUser: string;
  busy: boolean;
  actionError: string | null;
}>();

defineEmits<{ (e: "act", action: Action): void }>();
</script>

<template>
  <section class="panel">
    <div v-if="!item" class="empty">
      Select an item from the queue to see details.
    </div>
    <article v-else>
      <header class="head">
        <div>
          <div class="id">{{ item.id }}</div>
          <h1>{{ item.title }}</h1>
        </div>
        <span class="badge" :style="{ background: `var(--status-${item.status})` }">
          {{ item.status }}
        </span>
      </header>

      <dl class="facts">
        <div>
          <dt>Risk</dt>
          <dd>
            <span class="risk-dot" :style="{ background: `var(--risk-${item.risk_level})` }" />
            {{ item.risk_level }}
          </dd>
        </div>
        <div>
          <dt>Customer tier</dt>
          <dd>{{ item.customer_tier }}</dd>
        </div>
        <div>
          <dt>Submitted</dt>
          <dd>{{ new Date(item.submitted_at).toLocaleString() }}</dd>
        </div>
        <div>
          <dt>Assigned reviewer</dt>
          <dd>{{ item.assigned_reviewer ?? "—" }}</dd>
        </div>
        <div>
          <dt>Notes</dt>
          <dd>{{ item.notes_count }}</dd>
        </div>
      </dl>

      <h3>Summary</h3>
      <p class="summary">{{ item.summary }}</p>

      <ActionBar
        :item="item"
        :current-user="currentUser"
        :busy="busy"
        @act="(a) => $emit('act', a)"
      />
      <p v-if="actionError" class="error">{{ actionError }}</p>
    </article>
  </section>
</template>

<style scoped>
.panel {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: var(--space-5);
  min-height: 320px;
}
.empty { color: var(--text-muted); font-style: italic; }
.head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--space-3);
  margin-bottom: var(--space-4);
}
.id { font-size: 12px; color: var(--text-muted); letter-spacing: 0.05em; }
h1 { margin: 0; font-size: 20px; }
h3 { margin: var(--space-4) 0 var(--space-2); font-size: 14px; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-muted); }
.summary { margin: 0; }
.facts {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: var(--space-3);
  margin: 0;
  padding: var(--space-3);
  background: #f8f9fb;
  border-radius: var(--radius);
}
.facts > div { display: flex; flex-direction: column; gap: 2px; }
dt { font-size: 11px; text-transform: uppercase; color: var(--text-muted); letter-spacing: 0.05em; }
dd { margin: 0; text-transform: capitalize; display: flex; align-items: center; gap: var(--space-2); }
.risk-dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; }
.error {
  margin-top: var(--space-3);
  color: var(--risk-high);
  background: #fef2f2;
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius);
}
</style>
