import axios from "axios";

const api = axios.create({
  baseURL: "/api",
  timeout: 60000,  // AI 响应可能需要 5-30 秒
});

// ======================== 电影 ========================

/**
 * 获取电影基础列表（分页 + 搜索）
 * @param {string} q - 搜索关键词
 * @param {number} page - 页码
 * @param {number} pageSize - 每页大小
 * @returns {{ items: Array, total: number, page: number, page_size: number, pages: number }}
 */
export async function getMovieList(q = "", page = 1, pageSize = 30) {
  const { data } = await api.get("/movies", { params: { q, page, page_size: pageSize } });
  return data;
}

/**
 * 获取电影完整信息（分页 + 搜索 + 筛选 + 排序）
 * @param {Object} params
 * @param {string} params.q - 搜索关键词
 * @param {string} params.genre - 类型筛选
 * @param {string} params.country - 国家筛选
 * @param {number} params.yearMin - 年份下限
 * @param {number} params.yearMax - 年份上限
 * @param {number} params.ratingMin - 评分下限
 * @param {number} params.ratingMax - 评分上限
 * @param {string} params.sortBy - 排序字段
 * @param {number} params.page - 页码
 * @param {number} params.pageSize - 每页大小
 * @returns {{ items: Array, total: number, page: number, page_size: number, pages: number }}
 */
export async function getMovieListRich(params = {}) {
  const apiParams = {};
  if (params.q) apiParams.q = params.q;
  if (params.genre) apiParams.genre = params.genre;
  if (params.country) apiParams.country = params.country;
  if (params.yearMin != null) apiParams.year_min = params.yearMin;
  if (params.yearMax != null) apiParams.year_max = params.yearMax;
  if (params.ratingMin != null) apiParams.rating_min = params.ratingMin;
  if (params.ratingMax != null) apiParams.rating_max = params.ratingMax;
  if (params.sortBy) apiParams.sort_by = params.sortBy;
  apiParams.page = params.page || 1;
  apiParams.page_size = params.pageSize || 30;
  const { data } = await api.get("/movies/rich", { params: apiParams });
  return data;
}

/**
 * 获取单部电影详情
 * @param {string} movieId - 豆瓣 movie_id
 */
export async function getMovieDetail(movieId) {
  const { data } = await api.get(`/movie/${movieId}`);
  return data;
}

/**
 * 获取随机一部高分电影（Hero 展示用）
 */
export async function getRandomMovie() {
  const { data } = await api.get("/movies/random");
  return data;
}

/**
 * 获取首页轮播电影列表（随机 N 部高分电影）
 * @param {number} n - 返回数量，默认 10
 */
export async function getBannerMovies(n = 10) {
  const { data } = await api.get("/movies/banner", { params: { n } });
  return data;
}

// ======================== 推荐 ========================

/**
 * 按电影 ID 获取相似推荐
 * @param {string} movieId - 豆瓣 movie_id
 * @param {number} topN  - 返回数量
 */
export async function getSimilarMovies(movieId, topN = 12) {
  const { data } = await api.get(`/recommend/similar/${movieId}`, {
    params: { top_n: topN },
  });
  return data;
}

/**
 * 按文本搜索电影
 * @param {string} query - 搜索文本
 * @param {number} topN  - 返回数量
 */
export async function searchMovies(query, topN = 12) {
  const { data } = await api.post("/recommend/search", {
    query,
    top_n: topN,
  });
  return data;
}

// ======================== 数据分析 ========================

/**
 * 获取统计数据（总电影数、平均评分等）
 * 当前为 mock 数据，后续接入 GET /api/stats
 */
export async function getStats() {
  try {
    const { data } = await api.get("/stats");
    return data;
  } catch {
    // 后端未实现时返回 mock 数据
    return mockStats();
  }
}

// ======================== 智能问答 ========================

/**
 * 获取会话历史记录
 * @param {string} sessionId - 会话 ID
 */
export async function getChatHistory(sessionId) {
  const { data } = await api.get(`/chat/session/${encodeURIComponent(sessionId)}`);
  return data;
}

/**
 * 发送消息给智能问答机器人
 * @param {string} message - 用户消息
 * @param {Array} history - 历史消息 [{role, content}]（兼容旧版）
 * @param {string} sessionId - 会话 ID，用于服务端记忆
 */
export async function sendChatMessage(message, history = [], sessionId = null) {
  const body = { message, history };
  if (sessionId) body.session_id = sessionId;
  const { data } = await api.post("/chat", body);
  return data;
}

/**
 * 清除服务端会话历史
 * @param {string} sessionId - 会话 ID
 */
export async function clearChatSession(sessionId) {
  const { data } = await api.delete(`/chat/session/${encodeURIComponent(sessionId)}`);
  return data;
}

// ======================== Mock 数据 ========================

function mockStats() {
  return {
    total_movies: 2065,
    avg_rating: 7.46,
    top_movie: { title: "肖申克的救赎", rating: 9.7 },
    latest_year: 2026,
    year_span: 95,
  };
}
