// Thin fetch wrapper. The API key is kept in localStorage and sent as
// X-Api-Key on every request (the backend leaves /api/health unauthenticated).

const KEY_STORAGE = "bingearr_api_key";

export function getApiKey() {
  return localStorage.getItem(KEY_STORAGE) || "";
}

export function setApiKey(key) {
  localStorage.setItem(KEY_STORAGE, key);
}

async function req(path, opts = {}) {
  const headers = { "Content-Type": "application/json", ...(opts.headers || {}) };
  const key = getApiKey();
  if (key) headers["X-Api-Key"] = key;

  const res = await fetch(path, { ...opts, headers });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`${res.status} ${res.statusText}${text ? ` — ${text}` : ""}`);
  }
  if (res.status === 204) return null;
  const ct = res.headers.get("content-type") || "";
  return ct.includes("application/json") ? res.json() : res.text();
}

export const api = {
  health: () => req("/api/health"),
  listServers: () => req("/api/servers"),
  createServer: (body) =>
    req("/api/servers", { method: "POST", body: JSON.stringify(body) }),
  deleteServer: (id) => req(`/api/servers/${id}`, { method: "DELETE" }),
  testServer: (id) => req(`/api/servers/${id}/test`, { method: "POST" }),
  listMarathons: () => req("/api/marathons"),
};
