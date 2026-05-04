<script setup lang="ts">
import { computed } from "vue";
import { availableActions } from "../policy";
import type { Action, ReviewItem } from "../types";

const props = defineProps<{
  item: ReviewItem;
  currentUser: string;
  busy: boolean;
}>();

defineEmits<{ (e: "act", action: Action): void }>();

const policy = computed(() => availableActions(props.item, props.currentUser));

const ALL_IN_REVIEW: Action[] = ["approve", "reject", "escalate"];

const buttons = computed<Action[]>(() => {
  if (props.item.status === "in_review") return ALL_IN_REVIEW;
  if (props.item.status === "unassigned") return ["claim"];
  return [];
});

function isEnabled(action: Action): boolean {
  return policy.value.available.includes(action);
}

function label(action: Action): string {
  return action.charAt(0).toUpperCase() + action.slice(1);
}
</script>

<template>
  <div class="bar">
    <div v-if="policy.terminalMessage" class="terminal">
      {{ policy.terminalMessage }}
    </div>

    <template v-else>
      <button
        v-for="action in buttons"
        :key="action"
        :disabled="busy || !isEnabled(action)"
        @click="$emit('act', action)"
      >
        {{ label(action) }}
      </button>
      <span v-if="policy.disabledReason" class="hint">
        {{ policy.disabledReason }}
      </span>
    </template>
  </div>
</template>

<style scoped>
.bar {
  display: flex;
  gap: var(--space-2);
  align-items: center;
  flex-wrap: wrap;
  margin-top: var(--space-3);
}
.terminal {
  background: #f1f3f6;
  padding: var(--space-3);
  border-radius: var(--radius);
  width: 100%;
  color: var(--text-muted);
}
.hint { color: var(--text-muted); font-size: 12px; }
</style>
