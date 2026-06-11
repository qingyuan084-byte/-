import { ref, computed } from "vue";
import { searchMovies } from "@/api/index.js";
import { formatGenres } from "@/composables/useMovies.js";

export function useSearch(baseMovies) {
  const searchText = ref("");
  const searchQuery = ref("");
  const isSearching = ref(false);
  const searchResults = ref([]);
  const activeTag = ref("");
  const activeTagLabel = ref("");
  const expandedSection = ref(null);
  const searchLoading = ref(false);

  const filteredMovies = computed(() => {
    if (isSearching.value) return searchResults.value;
    if (activeTag.value) {
      const tag = activeTag.value;
      return baseMovies.value.filter((m) => {
        const gs = formatGenres(m.genres);
        return gs.split(" · ").some((g) => g.trim() === tag);
      });
    }
    return [];
  });

  async function onSearch() {
    const q = searchText.value.trim();
    if (!q) return;

    searchQuery.value = q;
    isSearching.value = true;
    activeTag.value = "";
    activeTagLabel.value = "";
    expandedSection.value = null;
    searchLoading.value = true;
    searchResults.value = [];

    try {
      const data = await searchMovies(q, 50);
      if (data && data.movies && data.movies.length > 0) {
        searchResults.value = data.movies.map((m) => ({
          ...m,
          poster_url: m.poster_url || "",
          similarity_score: m.similarity_score ?? 0,
        }));
      } else {
        localFallback(q);
      }
    } catch {
      localFallback(q);
    } finally {
      searchLoading.value = false;
    }

    window.scrollTo({ top: 400, behavior: "smooth" });
  }

  function localFallback(q) {
    const lower = q.toLowerCase();
    searchResults.value = baseMovies.value.filter(
      (m) =>
        m.title.toLowerCase().includes(lower) ||
        formatGenres(m.genres).toLowerCase().includes(lower) ||
        (m.summary || "").toLowerCase().includes(lower)
    );
  }

  function clearFilter() {
    isSearching.value = false;
    activeTag.value = "";
    activeTagLabel.value = "";
    searchResults.value = [];
    searchQuery.value = "";
    expandedSection.value = null;
    searchText.value = "";
  }

  function expandSection(key) {
    expandedSection.value = expandedSection.value === key ? null : key;
  }

  return {
    searchText, searchQuery, isSearching, searchResults,
    activeTag, activeTagLabel, expandedSection, searchLoading,
    filteredMovies, onSearch, clearFilter, expandSection,
  };
}
