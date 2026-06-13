<template>
  <div class="star-rating" :class="{ readonly: readonly }" @mouseleave="hoverRating = 0">
    <button
      v-for="star in 5"
      :key="star"
      class="star-btn"
      :tabindex="readonly ? -1 : 0"
      @mousemove="!readonly && onHover(star, $event)"
      @click="!readonly && onClick(star, $event)"
    >
      <span class="star-bg">☆</span>
      <span class="star-fg" :style="{ width: fillPct(star) + '%' }">
        <span class="star-fg-inner">★</span>
      </span>
    </button>
    <span v-if="showLabel" class="rating-label">{{ labelText }}</span>
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

const hoverRating = ref(0);

const displayRating = computed(() => hoverRating.value || props.modelValue);

function fillPct(star) {
  const dr = displayRating.value;
  if (dr >= star) return 100;
  if (dr >= star - 0.5) return 50;
  return 0;
}

function onHover(star, e) {
  const half = e.offsetX < e.currentTarget.offsetWidth / 2;
  hoverRating.value = half ? star - 0.5 : star;
}

function onClick(star, e) {
  const half = e.offsetX < e.currentTarget.offsetWidth / 2;
  const val = half ? star - 0.5 : star;
  emit("update:modelValue", val);
  emit("rate", val);
}

const LABELS = ["", "太差了", "较差", "一般", "推荐", "力荐"];
const labelText = computed(() => {
  if (!props.modelValue) return "";
  const n = Math.round(props.modelValue);
  return `${props.modelValue.toFixed(1)} — ${LABELS[n] || ""}`;
});
</script>

<style scoped>
.star-rating {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  user-select: none;
  -webkit-user-select: none;
}
.star-btn {
  position: relative;
  width: 30px;
  height: 30px;
  padding: 0;
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: 28px;
  line-height: 30px;
  text-align: center;
  overflow: hidden;
  transition: transform 0.15s ease;
  -webkit-tap-highlight-color: transparent;
}
.star-btn:focus-visible {
  outline: 2px solid var(--gold);
  outline-offset: 2px;
  border-radius: 4px;
}
.star-rating:not(.readonly) .star-btn:hover {
  transform: scale(1.15);
}
.star-bg {
  color: #374151;
  position: absolute;
  left: 0;
  top: 0;
  width: 100%;
  pointer-events: none;
  transition: color 0.15s ease;
}
.star-btn:hover .star-bg {
  color: #4b5563;
}
.star-fg {
  position: absolute;
  left: 0;
  top: 0;
  height: 100%;
  overflow: hidden;
  pointer-events: none;
  transition: width 0.1s ease;
}
.star-fg-inner {
  position: absolute;
  left: 0;
  top: 0;
  width: 30px;
  color: #f5c518;
  display: block;
}
.rating-label {
  margin-left: 8px;
  font-size: 13px;
  font-weight: 600;
  color: var(--gold);
  font-family: var(--font-display);
  white-space: nowrap;
  min-width: 90px;
}
</style>
