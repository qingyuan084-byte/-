import axios from "axios";

const api = axios.create({ baseURL: "/api", timeout: 10000 });

function authHeaders(token) {
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function register(username, password) {
  const { data } = await api.post("/auth/register", { username, password });
  return data;
}

export async function login(username, password) {
  const { data } = await api.post("/auth/login", { username, password });
  return data;
}

export async function logout(token) {
  const { data } = await api.post("/auth/logout", {}, { headers: authHeaders(token) });
  return data;
}

export async function checkAuth(token) {
  const { data } = await api.get("/auth/check", { headers: authHeaders(token) });
  return data;
}

export async function getProfile(token) {
  const { data } = await api.get("/auth/profile", { headers: authHeaders(token) });
  return data;
}

export async function toggleFavorite(token, movieId) {
  const { data } = await api.post(
    "/favorites/toggle",
    { movie_id: movieId },
    { headers: authHeaders(token) },
  );
  return data;
}

export async function getFavorites(token) {
  const { data } = await api.get("/favorites", { headers: authHeaders(token) });
  return data;
}

export async function getFavoriteMovies(token) {
  const { data } = await api.get("/favorites/detail", { headers: authHeaders(token) });
  return data;
}
