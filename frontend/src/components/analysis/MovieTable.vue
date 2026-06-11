<template>
  <section class="table-section">
    <h2 class="section-title"><span class="title-dot"></span>电影数据明细</h2>
    <div class="table-toolbar">
      <input
        :value="search"
        class="table-search"
        placeholder="搜索电影标题..."
        @input="$emit('update:search', $event.target.value)"
      />
      <span class="table-count">共 {{ filteredData.length }} 条</span>
    </div>
    <div class="table-wrap">
      <table class="data-table">
        <thead>
          <tr>
            <th @click="$emit('sort', 'title')" class="sortable">
              片名 <span class="sort-arrow">{{ sortCol === 'title' ? (sortDir === 'asc' ? '↑' : '↓') : '' }}</span>
            </th>
            <th @click="$emit('sort', 'rating')" class="sortable">
              评分 <span class="sort-arrow">{{ sortCol === 'rating' ? (sortDir === 'asc' ? '↑' : '↓') : '' }}</span>
            </th>
            <th @click="$emit('sort', 'year')" class="sortable">
              年份 <span class="sort-arrow">{{ sortCol === 'year' ? (sortDir === 'asc' ? '↑' : '↓') : '' }}</span>
            </th>
            <th>类型</th>
            <th>时长</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="m in pagedData" :key="m.movie_id" class="movie-row" @click="$emit('select', m.movie_id)">
            <td class="td-title">{{ m.title }}</td>
            <td>
              <span class="td-rating" :class="ratingClass(m.rating)">
                ★ {{ m.rating?.toFixed(1) }}
              </span>
            </td>
            <td>{{ m.year || '-' }}</td>
            <td class="td-genres">{{ truncateGenres(m.genres) }}</td>
            <td>{{ m.runtime || '-' }}</td>
          </tr>
        </tbody>
      </table>
    </div>
    <div class="table-footer">
      <el-pagination
        :current-page="page"
        :page-size="pageSize"
        :total="filteredData.length"
        layout="prev, pager, next"
        background
        small
        @current-change="$emit('update:page', $event)"
      />
    </div>
  </section>
</template>

<script setup>
defineProps({
  search: { type: String, default: "" },
  filteredData: { type: Array, default: () => [] },
  pagedData: { type: Array, default: () => [] },
  page: { type: Number, default: 1 },
  pageSize: { type: Number, default: 15 },
  sortCol: { type: String, default: "rating" },
  sortDir: { type: String, default: "desc" },
});
defineEmits(["update:search", "update:page", "sort", "select"]);

function ratingClass(r) {
  if (r >= 8.5) return "high";
  if (r >= 7) return "mid";
  return "low";
}
function truncateGenres(g) {
  if (!g) return "-";
  const arr = Array.isArray(g) ? g : String(g).split(/[,，]/);
  return arr.map((x) => x.trim()).filter(Boolean).slice(0, 3).join(" · ") || "-";
}
</script>

<style scoped>
.table-section { margin-top: 40px; }
.section-title {
  font-family: var(--font-display, 'Georgia', serif);
  font-size: 20px; font-weight: 700; color: var(--text-primary);
  display: flex; align-items: center; gap: 10px; margin-bottom: 20px;
}
.title-dot {
  width: 8px; height: 8px; border-radius: 50%;
  background: var(--gold); display: inline-block;
}
.table-toolbar { display: flex; align-items: center; gap: 16px; margin-bottom: 16px; }
.table-search {
  padding: 8px 14px; border-radius: 8px; border: 1px solid var(--border-subtle);
  background: var(--bg-elevated); color: var(--text-primary); font-size: 13px;
  font-family: inherit; width: 240px; outline: none; transition: border-color 0.2s;
}
.table-search:focus { border-color: var(--gold); }
.table-search::placeholder { color: var(--text-muted); }
.table-count { font-size: 12px; color: var(--text-muted); }
.table-wrap { overflow-x: auto; border-radius: var(--radius-md, 12px); border: 1px solid var(--border-subtle); }
.data-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.data-table thead { background: var(--bg-surface); }
.data-table th {
  padding: 12px 16px; text-align: left; font-weight: 600;
  color: var(--text-secondary); font-size: 12px; text-transform: uppercase;
  letter-spacing: 0.04em; white-space: nowrap;
}
.data-table th.sortable { cursor: pointer; user-select: none; }
.data-table th.sortable:hover { color: var(--gold); }
.sort-arrow { color: var(--gold); font-size: 11px; }
.data-table td { padding: 11px 16px; border-top: 1px solid var(--border-subtle); color: var(--text-primary); }
.data-table tbody tr { transition: background 0.15s; }
.data-table tbody tr:hover { background: var(--bg-surface); }
.movie-row { cursor: pointer; }
.td-title { max-width: 260px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-weight: 500; }
.td-rating { font-weight: 700; font-family: var(--font-display, 'Georgia', serif); }
.td-rating.high { color: #22C55E; }
.td-rating.mid { color: var(--gold); }
.td-rating.low { color: var(--text-muted); }
.td-genres { max-width: 180px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; color: var(--text-secondary); font-size: 12px; }
.table-footer { display: flex; justify-content: center; margin-top: 20px; }
@media (max-width: 768px) { .table-search { width: 160px; } }
</style>
