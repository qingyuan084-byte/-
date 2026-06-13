<template>
  <div class="star-rating" @mouseleave="hovered = 0">
    <button
      v-for="i in 10"
      :key="i"
      :class="starClass(i)"
      :title="i % 2 === 0 ? `${i / 2} 星` : `${(i / 2).toFixed(1)} 星`"
      :aria-label="`${(i / 2).toFixed(i % 2 === 0 ? 0 : 1)} 星`"
      class="star-btn"
      @mousemove.prevent="hovered = i"
      @click.stop="onClick(i)"
    >
      {{ starChar(i) }}
    </button>
    <span v-if="showLabel" class="rating-label">{{ displayLabel }}</span>
  </div>
</template>

<script setup>
import { ref, computed } from "vue";

const props = defineProps({
  modelValue: { type: Number, default: 0 },
  readonly: { type: Boolean, default: false },
  showLabel: { type: Boolean, default: false },
});

const emit = defineEmits(["update:modelValue", "rate"]);

const hovered = ref(0);
const active = computed(() => hovered.value || Math.round(props.modelValue * 2));

function starChar(i) {
  const val = active.value;
  if (i <= val) return "★";
  return "☆";
}

function starClass(i) {
  const val = active.value;
  if (i <= val) return "star-btn filled";
  return "star-btn";
}

function onClick(i) {
  if (props.readonly) return;
  const rating = i / 2;
  emit("update:modelValue", rating);
  emit("rate", rating);
}

const LABELS = ["", "太差了", "较差", "一般", "推荐", "力荐"];
const displayLabel = computed(() => {
  if (!props.modelValue) return "";
  const n = Math.round(props.modelValue);
  return `${props.modelValue.toFixed(1)} — ${LABELS[n] || ""}`;
});
</script>

<style scoped>
.star-rating {
  display: inline-flex;
  align-items: center;
  gap: 1px;
  user-select: none;
  -webkit-user-select: none;
}
.star-btn {
  position: relative;
  width: 28px;
  height: 28px;
  padding: 0;
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: 26px;
  line-height: 1;
  transition: transform 0.15s ease, color 0.15s ease;
  color: #374151;
  overflow: hidden;
}
.star-btn:hover {
  transform: scale(1.2);
}
.star-btn.filled {
  color: #f5c518;
}
/* 奇数按钮 = 半星：裁剪50% */
.star-btn:nth-child(odd) {
  width: 14px;
  direction: ltr;
}
.star-btn:nth-child(even) {
  width: 14px;
  direction: rtl;
}
.rating-label {
  margin-left: 10px;
  font-size: 13px;
  font-weight: 600;
  color: var(--gold);
  font-family: var(--font-display);
  white-space: nowrap;
}
</style>
