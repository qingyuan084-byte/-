import { ref, nextTick, watch, onMounted } from "vue";
import { sendChatMessage, clearChatSession, getChatHistory } from "@/api/index.js";

const SESSION_KEY = "cinematic_chat_session_id";

function getOrCreateSessionId() {
  let id = localStorage.getItem(SESSION_KEY);
  if (!id) {
    id = "sess-" + Date.now().toString(36) + "-" + Math.random().toString(36).slice(2, 8);
    localStorage.setItem(SESSION_KEY, id);
  }
  return id;
}

/** 消息持久化：localStorage 作为快速缓存，服务端 SQLite 为权威数据源。 */
function loadLocalMessages(sessionId) {
  try {
    const raw = localStorage.getItem(`chat_msgs_${sessionId}`);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function saveLocalMessages(sessionId, messages) {
  try {
    localStorage.setItem(`chat_msgs_${sessionId}`, JSON.stringify(messages));
  } catch {}
}

function clearLocalMessages(sessionId) {
  try {
    localStorage.removeItem(`chat_msgs_${sessionId}`);
  } catch {}
}

export function useChat() {
  const sessionId = getOrCreateSessionId();
  const messages = ref(loadLocalMessages(sessionId));
  const inputText = ref("");
  const isTyping = ref(false);
  const messagesEl = ref(null);
  const inputEl = ref(null);
  const hasRestored = ref(false);

  function formatTime() {
    const now = new Date();
    return `${String(now.getHours()).padStart(2, "0")}:${String(now.getMinutes()).padStart(2, "0")}`;
  }

  async function scrollToBottom() {
    await nextTick();
    if (messagesEl.value) {
      messagesEl.value.scrollTo({
        top: messagesEl.value.scrollHeight,
        behavior: "smooth",
      });
    }
  }

  function escapeRegex(str) {
    return str.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  }

  function formatReplyWithLinks(reply, relatedMovies) {
    if (!reply || !relatedMovies || relatedMovies.length === 0) return reply;
    let result = reply;
    relatedMovies.forEach((movie) => {
      const title = movie.title;
      const regex = new RegExp(`《${escapeRegex(title)}》`, "g");
      const link = `<a href="/movie/${movie.movie_id}" class="movie-link" data-movie-id="${movie.movie_id}">《${title}》</a>`;
      result = result.replace(regex, link);
    });
    return result;
  }

  function renderContent(text, relatedMovies) {
    if (!text) return "";
    let html = formatReplyWithLinks(text, relatedMovies);
    return html
      .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
      .replace(/\n/g, "<br>")
      .replace(/🎬|🎥|💎|🥇|🥈|🥉/g, (match) => `<span class="emoji">${match}</span>`);
  }

  function mapMovieCard(m) {
    return {
      ...m,
      similarity_score: m.similarity_score ?? m.similarity ?? 0,
      poster_url: m.poster_url || "",
    };
  }

  // ── 从服务端恢复历史记录 ──────────────────────
  async function restoreHistory() {
    if (hasRestored.value) return;
    try {
      const data = await getChatHistory(sessionId);
      if (data.history && data.history.length > 0) {
        // 服务端存储的只有 {role, content}，没有 time/relatedMovies
        // 如果本地已有更完整的数据（含 time），优先保留本地
        const localMsgs = loadLocalMessages(sessionId);
        if (localMsgs.length >= data.history.length) {
          messages.value = localMsgs;
        } else {
          // 服务端有更多消息，合并
          messages.value = data.history.map((m) => ({
            ...m,
            time: formatTime(),
            relatedMovies: m.related_movies || [],
          }));
          saveLocalMessages(sessionId, messages.value);
        }
      }
    } catch {
      // 服务端不可用时，已从 localStorage 恢复了
    } finally {
      hasRestored.value = true;
    }
  }

  // 消息变化时自动保存到 localStorage
  watch(messages, (val) => {
    saveLocalMessages(sessionId, val);
  }, { deep: true });

  async function sendMessage(text) {
    if (!text || isTyping.value) return;

    messages.value = [...messages.value, {
      role: "user",
      content: text,
      time: formatTime(),
    }];
    inputText.value = "";
    await scrollToBottom();

    isTyping.value = true;
    await scrollToBottom();

    try {
      const data = await sendChatMessage(text, [], sessionId);
      messages.value = [...messages.value, {
        role: "assistant",
        content: data.reply || "抱歉，我暂时无法回答这个问题。",
        time: formatTime(),
        relatedMovies: data.related_movies || [],
      }];
    } catch {
      messages.value = [...messages.value, {
        role: "assistant",
        content: "服务暂时不可用，请稍后重试。",
        time: formatTime(),
        relatedMovies: [],
      }];
    } finally {
      isTyping.value = false;
      await scrollToBottom();
      inputEl.value?.focus();
    }
  }

  async function startNewChat() {
    try {
      await clearChatSession(sessionId);
    } catch {}
    messages.value = [];
    clearLocalMessages(sessionId);
    inputEl.value?.focus();
  }

  return {
    messages, inputText, isTyping, sessionId,
    messagesEl, inputEl,
    sendMessage, startNewChat, restoreHistory,
    renderContent, mapMovieCard, formatTime,
    scrollToBottom,
  };
}
