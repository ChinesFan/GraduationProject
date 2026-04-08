export const API_BASE = "http://127.0.0.1:5000";

export function getToken() {
  return localStorage.getItem("token") || "";
}

export function authHeaders(extra = {}) {
  const token = getToken();
  return {
    Authorization: `Bearer ${token}`,
    ...extra,
  };
}
