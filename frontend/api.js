const API_BASE = "http://localhost:8000";

// Token en memoria — nunca en localStorage
window._token = null;

export function setToken(t) { window._token = t; }
export function clearToken() { window._token = null; }

export async function api(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  if (window._token) headers["Authorization"] = `Bearer ${window._token}`;

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });

  if (res.status === 401) {
    clearToken();
    window.location.reload();
    return;
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Error desconocido");
  }

  return res.json();
}

window.api = api;
window.setToken = setToken;
window.clearToken = clearToken;
