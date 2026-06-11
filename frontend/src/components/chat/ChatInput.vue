<template>
  <div class="chat-input-area">
    <div class="input-row">
      <input
        :value="modelValue"
        class="chat-input"
        placeholder="输入你的问题，如：推荐几部悬疑烧脑的电影..."
        @keyup.enter="$emit('send')"
        @input="$emit('update:modelValue', $event.target.value)"
        :disabled="disabled"
        ref="inputRef"
      />
      <button
        class="send-btn"
        :disabled="!modelValue.trim() || disabled"
        @click="$emit('send')"
        title="发送"
      >
        <span class="send-icon">↑</span>
      </button>
    </div>
    <p class="input-hint">
      <span>Enter 发送</span>
      <span class="hint-divider">·</span>
      <span>登小千 由智谱AI GLM 大模型驱动</span>
    </p>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";

defineProps({
  modelValue: { type: String, default: "" },
  disabled: { type: Boolean, default: false },
});
defineEmits(["update:modelValue", "send"]);

const inputRef = ref(null);
onMounted(() => {
  inputRef.value?.focus();
});
defineExpose({ inputRef });
</script>

<style scoped>
.chat-input-area {
  padding: 16px 20px 12px;
  border-top: 1px solid var(--border-subtle);
  background: var(--bg-deep);
}
.input-row {
  display: flex;
  gap: 10px;
  align-items: center;
}
.chat-input {
  flex: 1;
  padding: 12px 16px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-default);
  background: var(--bg-surface);
  color: var(--text-primary);
  font-size: 14px;
  font-family: var(--font-body);
  outline: none;
  transition: all var(--duration-fast) var(--ease-out);
}
.chat-input::placeholder {
  color: var(--text-muted);
}
.chat-input:focus {
  border-color: var(--gold);
  box-shadow: 0 0 0 3px var(--gold-subtle);
}
.chat-input:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.send-btn {
  width: 42px;
  height: 42px;
  border-radius: var(--radius-md);
  border: none;
  background: var(--gold);
  color: var(--text-inverse);
  font-size: 18px;
  font-weight: 700;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all var(--duration-base) var(--ease-out);
}
.send-btn:hover:not(:disabled) {
  background: var(--gold-bright);
  box-shadow: var(--shadow-gold);
  transform: translateY(-1px);
}
.send-btn:active:not(:disabled) {
  transform: scale(0.95);
}
.send-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}
.send-icon { line-height: 1; }
.input-hint {
  display: flex;
  justify-content: center;
  gap: 8px;
  margin-top: 8px;
  font-size: 11px;
  color: var(--text-muted);
}
.hint-divider { opacity: 0.4; }
</style>
