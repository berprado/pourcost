const API_BASE = "http://localhost:8000";

// Locale Bolivia: Bs 1.234,56
const LOCALE = 'es-BO';

export function fmtBs(v) {
  if (v == null) return "—";
  return "Bs " + new Intl.NumberFormat(LOCALE, { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(v);
}

export function fmtPct(v) {
  if (!v) return "—";
  return new Intl.NumberFormat(LOCALE, { minimumFractionDigits: 1, maximumFractionDigits: 1 }).format(v * 100) + "%";
}

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
window.fmtBs = fmtBs;
window.fmtPct = fmtPct;
