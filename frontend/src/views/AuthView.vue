<template>
  <div class="auth-view">
    <div class="auth-card glass">
      <div class="auth-header">
        <h1>{{ isLoginMode ? "登录" : "注册" }}</h1>
        <p class="toggle-text">
          {{ isLoginMode ? "还没有账号？" : "已有账号？" }}
          <button class="toggle-btn" @click="toggleMode">
            {{ isLoginMode ? "立即注册" : "去登录" }}
          </button>
        </p>
      </div>

      <form class="auth-form" @submit.prevent="handleSubmit">
        <div class="form-field">
          <label class="field-label">用户名</label>
          <input
            v-model="username"
            class="field-input"
            type="text"
            placeholder="输入用户名"
            autocomplete="username"
            maxlength="30"
          />
        </div>

        <div class="form-field">
          <label class="field-label">密码</label>
          <input
            v-model="password"
            class="field-input"
            type="password"
            placeholder="输入密码"
            autocomplete="current-password"
            maxlength="100"
          />
        </div>

        <div v-if="!isLoginMode" class="form-field">
          <label class="field-label">确认密码</label>
          <input
            v-model="confirmPassword"
            class="field-input"
            type="password"
            placeholder="再次输入密码"
            autocomplete="new-password"
          />
        </div>

        <p v-if="errorMsg" class="error-msg">{{ errorMsg }}</p>

        <button
          class="submit-btn"
          type="submit"
          :disabled="loading || !canSubmit"
        >
          {{ loading ? "处理中…" : isLoginMode ? "登录" : "注册" }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useAuth } from "@/composables/useAuth.js";

const route = useRoute();
const router = useRouter();
const { login, register } = useAuth();

const isLoginMode = ref(true);
const username = ref("");
const password = ref("");
const confirmPassword = ref("");
const loading = ref(false);
const errorMsg = ref("");

const canSubmit = computed(() => {
  if (!username.value.trim() || !password.value) return false;
  if (username.value.trim().length < 3) return false;
  if (password.value.length < 6) return false;
  if (!isLoginMode.value && password.value !== confirmPassword.value) return false;
  return true;
});

function toggleMode() {
  isLoginMode.value = !isLoginMode.value;
  errorMsg.value = "";
  confirmPassword.value = "";
}

async function handleSubmit() {
  errorMsg.value = "";
  if (!canSubmit.value) return;

  loading.value = true;
  try {
    const fn = isLoginMode.value ? login : register;
    const result = await fn(username.value.trim(), password.value);
    if (result.success) {
      const redirect = route.query.redirect || "/home";
      router.push(redirect);
    } else {
      errorMsg.value = result.message;
    }
  } catch {
    errorMsg.value = "网络错误，请稍后重试";
  }
  loading.value = false;
}
</script>

<style scoped>
.auth-view {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 70vh;
  padding: 24px;
}

.auth-card {
  width: 100%;
  max-width: 420px;
  border-radius: var(--radius-xl);
  padding: 40px 36px;
  background: var(--bg-elevated);
  border: 1px solid var(--border-subtle);
}

.auth-header {
  text-align: center;
  margin-bottom: 32px;
}

.auth-header h1 {
  font-family: var(--font-display);
  font-size: 28px;
  font-weight: 800;
  color: var(--text-primary);
  margin-bottom: 10px;
}

.toggle-text {
  font-size: 14px;
  color: var(--text-secondary);
}

.toggle-btn {
  background: none;
  border: none;
  color: var(--gold);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  font-family: inherit;
  padding: 0;
  text-decoration: underline;
  text-underline-offset: 3px;
}

.toggle-btn:hover {
  color: var(--gold-bright);
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
}

.field-input {
  padding: 10px 14px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-subtle);
  background: var(--bg-surface);
  color: var(--text-primary);
  font-size: 14px;
  font-family: inherit;
  outline: none;
  transition: border-color 0.2s;
}

.field-input:focus {
  border-color: var(--gold);
  box-shadow: 0 0 0 3px var(--gold-subtle);
}

.field-input::placeholder {
  color: var(--text-muted);
}

.error-msg {
  font-size: 13px;
  color: #f87171;
  margin: 0;
}

.submit-btn {
  margin-top: 4px;
  padding: 12px 0;
  border-radius: var(--radius-md);
  border: none;
  background: var(--gold);
  color: #fff;
  font-size: 15px;
  font-weight: 700;
  font-family: inherit;
  cursor: pointer;
  transition: all 0.2s;
}

.submit-btn:hover:not(:disabled) {
  background: var(--gold-bright);
  box-shadow: 0 4px 16px var(--gold-glow);
}

.submit-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
