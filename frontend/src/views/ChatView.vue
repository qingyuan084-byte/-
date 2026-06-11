<template>
  <div class="chat-view">
    <section class="chat-hero">
      <div class="hero-top">
        <h1 class="chat-title">
          <span class="title-accent">◉</span>
          智能电影问答
        </h1>
        <button
          v-if="messages.length > 0"
          class="new-chat-btn"
          @click="startNewChat"
          title="开始新对话"
        >
          + 新对话
        </button>
      </div>
      <p class="chat-desc">
        向 AI 助手提问，获取个性化电影推荐与分析
      </p>
    </section>

    <div class="chat-container glass">
      <div class="chat-messages" ref="messagesEl" @click="onMessageClick">
        <!-- 欢迎消息 -->
        <div v-if="messages.length === 0" class="welcome-wrap">
          <QuickPrompts :questions="quickQuestions" @select="sendQuick" />
        </div>

        <!-- 消息列表 -->
        <ChatMessages
          :messages="messages"
          :render-content="renderContent"
          :map-movie-card="mapMovieCard"
        />

        <!-- 正在输入动画 -->
        <div v-if="isTyping" class="message-row assistant">
          <div class="avatar bot-avatar"><span>🎬</span></div>
          <div class="bubble-wrap">
            <div class="bubble assistant typing-bubble">
              <span class="typing-dots"><i></i><i></i><i></i></span>
            </div>
          </div>
        </div>
      </div>

      <ChatInput
        v-model="inputText"
        :disabled="isTyping"
        @send="onSend"
      />
    </div>
  </div>
</template>

<script setup>
import { onMounted } from "vue";
import { useRouter } from "vue-router";
import QuickPrompts from "@/components/chat/QuickPrompts.vue";
import ChatMessages from "@/components/chat/ChatMessages.vue";
import ChatInput from "@/components/chat/ChatInput.vue";
import { useChat } from "@/composables/useChat.js";
import { pickRandomQuestions } from "@/utils/quickQuestions.js";

const router = useRouter();

const quickQuestions = pickRandomQuestions(4);

const {
  messages, inputText, isTyping,
  messagesEl,
  sendMessage, startNewChat, restoreHistory,
  renderContent, mapMovieCard,
} = useChat();

function sendQuick(q) {
  inputText.value = q;
  sendMessage(inputText.value);
}
function onSend() {
  sendMessage(inputText.value);
}

function onMessageClick(event) {
  const link = event.target.closest(".movie-link");
  if (!link) return;
  event.preventDefault();
  const movieId = link.dataset.movieId;
  if (movieId) router.push(`/movie/${movieId}`);
}

onMounted(() => {
  restoreHistory();
});
</script>

<style scoped>
.chat-view {
  max-width: 780px;
  margin: 0 auto;
}

.chat-hero {
  text-align: center;
  padding: 20px 0 28px;
}
.hero-top {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  flex-wrap: wrap;
}
.new-chat-btn {
  padding: 6px 16px;
  border-radius: 50px;
  border: 1px solid var(--gold-dim);
  background: transparent;
  color: var(--gold);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-out);
  font-family: var(--font-body);
  white-space: nowrap;
}
.new-chat-btn:hover {
  background: var(--gold-subtle);
  border-color: var(--gold);
  box-shadow: 0 0 12px var(--gold-glow);
}
.chat-title {
  font-family: var(--font-display);
  font-size: clamp(1.6rem, 4vw, 2.2rem);
  font-weight: 900;
  color: var(--text-primary);
  letter-spacing: 0.02em;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  margin-bottom: 8px;
}
.title-accent { color: var(--gold); }
.chat-desc {
  color: var(--text-secondary);
  font-size: 14px;
}

.chat-container {
  border-radius: var(--radius-xl);
  display: flex;
  flex-direction: column;
  height: calc(100vh - 280px);
  min-height: 500px;
  max-height: 700px;
  overflow: hidden;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 24px 24px 8px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.welcome-wrap {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px 0;
}

/* typing indicator */
.message-row { display: flex; gap: 10px; align-items: flex-end; max-width: 85%; }
.message-row.assistant { align-self: flex-start; }
.avatar {
  width: 36px; height: 36px; border-radius: 50%; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center; font-size: 16px;
}
.bot-avatar { background: linear-gradient(135deg, #f5c518 0%, #e8a817 100%); }
.bubble-wrap { display: flex; flex-direction: column; gap: 4px; min-width: 0; }
.bubble {
  padding: 12px 16px; border-radius: var(--radius-lg);
  font-size: 14px; line-height: 1.65; word-break: break-word;
}
.bubble.assistant {
  background: var(--bg-surface); border: 1px solid var(--border-subtle);
  border-bottom-left-radius: 4px; color: var(--text-primary);
}
.typing-bubble { padding: 14px 20px !important; }
.typing-dots { display: flex; gap: 5px; align-items: center; }
.typing-dots i {
  width: 6px; height: 6px; border-radius: 50%; background: var(--text-muted);
  animation: typeDot 1.4s ease-in-out infinite;
}
.typing-dots i:nth-child(2) { animation-delay: 0.2s; }
.typing-dots i:nth-child(3) { animation-delay: 0.4s; }
@keyframes typeDot {
  0%, 60%, 100% { transform: translateY(0); opacity: 0.3; }
  30% { transform: translateY(-6px); opacity: 1; }
}

@media (max-width: 768px) {
  .chat-container { height: calc(100vh - 200px); min-height: 400px; border-radius: var(--radius-lg); }
  .chat-messages { padding: 16px 14px 8px; }
}
</style>
