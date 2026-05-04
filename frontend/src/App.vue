<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import QueueList from "./components/QueueList.vue";
import DetailPanel from "./components/DetailPanel.vue";
import { TransitionError, fetchQueue, transition } from "./api";
import type { QueueView } from "./api";
import type { Action, ReviewItem } from "./types";

const CURRENT_USER = "alex";

const items = ref<ReviewItem[]>([]);
const selectedId = ref<string | null>(null);
const view = ref<QueueView>("active");
const loading = ref(true);
const error = ref<string | null>(null);
const actionError = ref<string | null>(null);
const busy = ref(false);
const banner = ref<string | null>(null);

const selected = computed<ReviewItem | null>(
  () => items.value.find((i) => i.id === selectedId.value) ?? null,
);

async function refresh() {
  try {
    items.value = await fetchQueue(view.value);
    error.value = null;
  } catch (e) {
    error.value = e instanceof Error ? e.message : "Failed to load queue.";
  } finally {
    loading.value = false;
  }
}

function onSelect(id: string) {
  selectedId.value = id;
  actionError.value = null;
  banner.value = null;
}

async function onViewChange(next: QueueView) {
  if (view.value === next) return;
  view.value = next;
  banner.value = null;
  await refresh();
}

async function onAct(action: Action) {
  if (!selectedId.value) return;
  const id = selectedId.value;
  busy.value = true;
  actionError.value = null;
  try {
    const updated = await transition(id, action);
    await refresh();
    if (!items.value.some((i) => i.id === id)) {
      banner.value = `${id} is now ${updated.status}.`;
      selectedId.value = null;
    } else if (view.value === "all") {
      banner.value = `${id} is now ${updated.status}.`;
    }
  } catch (e) {
    if (e instanceof TransitionError) {
      actionError.value = e.message;
    } else {
      actionError.value = "Action failed.";
    }
  } finally {
    busy.value = false;
  }
}

onMounted(refresh);
</script>

<template>
  <main class="layout">
    <header class="app-head">
      <h1>Reviewer queue</h1>
      <span class="me">Signed in as <strong>{{ CURRENT_USER }}</strong></span>
    </header>

    <p v-if="banner" class="banner">{{ banner }}</p>

    <div v-if="loading" class="state">Loading queue…</div>
    <div v-else-if="error" class="state error">{{ error }}</div>
    <div v-else class="grid">
      <QueueList
        :items="items"
        :selected-id="selectedId"
        :view="view"
        @select="onSelect"
        @view-change="onViewChange"
      />
      <DetailPanel
        :item="selected"
        :current-user="CURRENT_USER"
        :busy="busy"
        :action-error="actionError"
        @act="onAct"
      />
    </div>
  </main>
</template>

<style scoped>
.layout {
  max-width: 1200px;
  margin: 0 auto;
  padding: var(--space-5);
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}
.app-head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
}
h1 { margin: 0; font-size: 22px; }
.me { color: var(--text-muted); font-size: 13px; }
.grid {
  display: grid;
  grid-template-columns: minmax(320px, 420px) 1fr;
  gap: var(--space-4);
  align-items: start;
}
@media (max-width: 768px) {
  .grid { grid-template-columns: 1fr; }
}
.state {
  padding: var(--space-5);
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
}
.state.error { color: var(--risk-high); }
.banner {
  margin: 0;
  padding: var(--space-3);
  background: #ecfdf5;
  border: 1px solid #a7f3d0;
  border-radius: var(--radius);
  color: #065f46;
}
</style>
