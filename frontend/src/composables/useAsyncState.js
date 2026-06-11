import { ref } from "vue";

export function useAsyncState(fn) {
  const loading = ref(false);
  const error = ref("");
  const data = ref(null);

  async function execute(...args) {
    loading.value = true;
    error.value = "";
    try {
      data.value = await fn(...args);
      return data.value;
    } catch (e) {
      error.value = e?.message || "请求失败";
      return null;
    } finally {
      loading.value = false;
    }
  }

  return { loading, error, data, execute };
}
