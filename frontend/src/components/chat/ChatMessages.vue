<template>
  <div
    v-for="(msg, i) in messages"
    :key="i"
    class="message-row"
    :class="msg.role"
  >
    <div v-if="msg.role === 'assistant'" class="avatar bot-avatar">
      <span>🎬</span>
    </div>

    <div class="bubble-wrap">
      <div class="bubble" :class="msg.role">
        <div class="bubble-text" v-html="renderContent(msg.content, msg.relatedMovies)"></div>
      </div>
      <span class="bubble-time">{{ msg.time }}</span>

      <RelatedMovies
        v-if="msg.role === 'assistant' && msg.relatedMovies && msg.relatedMovies.length > 0"
        :movies="msg.relatedMovies"
        :map-fn="mapMovieCard"
      />
    </div>

    <div v-if="msg.role === 'user'" class="avatar user-avatar">
      <span>👤</span>
    </div>
  </div>
</template>

<script setup>
import RelatedMovies from "./RelatedMovies.vue";

defineProps({
  messages: { type: Array, default: () => [] },
  renderContent: { type: Function, required: true },
  mapMovieCard: { type: Function, required: true },
});
</script>

<style scoped>
.message-row {
  display: flex;
  gap: 10px;
  align-items: flex-end;
  max-width: 85%;
  animation: msgSlideIn 300ms var(--ease-out);
}
.message-row.user {
  align-self: flex-end;
  flex-direction: row-reverse;
}
.message-row.assistant {
  align-self: flex-start;
}
@keyframes msgSlideIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
.avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
}
.bot-avatar {
  background: linear-gradient(135deg, #f5c518 0%, #e8a817 100%);
}
.user-avatar {
  background: var(--bg-surface);
  border: 1px solid var(--border-default);
}
.bubble-wrap {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}
.bubble {
  padding: 12px 16px;
  border-radius: var(--radius-lg);
  font-size: 14px;
  line-height: 1.65;
  word-break: break-word;
}
.bubble.assistant {
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-bottom-left-radius: 4px;
  color: var(--text-primary);
}
.bubble.user {
  background: var(--gold-subtle);
  border: 1px solid var(--gold-glow);
  border-bottom-right-radius: 4px;
  color: var(--text-primary);
}
.bubble-text strong {
  color: var(--gold);
  font-weight: 700;
}
.bubble-text :deep(.emoji) {
  font-size: 1.1em;
}
.bubble-text :deep(.movie-link) {
  color: var(--gold);
  font-weight: 600;
  text-decoration: none;
  border-bottom: 1px dashed var(--gold);
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-out);
}
.bubble-text :deep(.movie-link:hover) {
  color: var(--gold-bright);
  border-bottom-style: solid;
  text-shadow: 0 0 8px var(--gold-glow);
}
.bubble-time {
  font-size: 11px;
  color: var(--text-muted);
  padding: 0 4px;
}
.message-row.user .bubble-time {
  text-align: right;
}
@media (max-width: 768px) {
  .message-row { max-width: 92%; }
}
</style>
