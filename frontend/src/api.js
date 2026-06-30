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

function qs(params) {
  const p = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== "") p.set(k, v);
  });
  const s = p.toString();
  return s ? `?${s}` : "";
}

export const api = {
  health: () => req("/api/health"),

  // Servers
  listServers: () => req("/api/servers"),
  createServer: (body) => req("/api/servers", { method: "POST", body: JSON.stringify(body) }),
  deleteServer: (id) => req(`/api/servers/${id}`, { method: "DELETE" }),
  testServer: (id) => req(`/api/servers/${id}/test`, { method: "POST" }),
  listLibraries: (id) => req(`/api/servers/${id}/libraries`),
  listItems: (id, libraryKey, { search, limit, offset } = {}) =>
    req(`/api/servers/${id}/libraries/${libraryKey}/items${qs({ search, limit, offset })}`),
  listCollections: (id, libraryKey) =>
    req(`/api/servers/${id}/libraries/${libraryKey}/collections`),
  expandCollection: (id, collectionId) =>
    req(`/api/servers/${id}/collections/${collectionId}/items`),
  expandShow: (id, showId, { order, unwatched_only } = {}) =>
    req(`/api/servers/${id}/shows/${showId}/episodes${qs({ order, unwatched_only })}`),
  listGenres: (id, libraryKey) => req(`/api/servers/${id}/libraries/${libraryKey}/genres`),
  smartSelect: (id, libraryKey, { genre, watch, minutes, max_items } = {}) =>
    req(`/api/servers/${id}/libraries/${libraryKey}/smart${qs({ genre, watch, minutes, max_items })}`),

  // Marathons
  listMarathons: () => req("/api/marathons"),
  getMarathon: (id) => req(`/api/marathons/${id}`),
  createMarathon: (body) => req("/api/marathons", { method: "POST", body: JSON.stringify(body) }),
  updateMarathon: (id, body) =>
    req(`/api/marathons/${id}`, { method: "PUT", body: JSON.stringify(body) }),
  deleteMarathon: (id) => req(`/api/marathons/${id}`, { method: "DELETE" }),
  pushMarathon: (id) => req(`/api/marathons/${id}/push`, { method: "POST" }),
  rebuildMarathon: (id) => req(`/api/marathons/${id}/rebuild`, { method: "POST" }),
  applyPreroll: (id) => req(`/api/marathons/${id}/preroll/apply`, { method: "POST" }),
  clearPreroll: (id) => req(`/api/marathons/${id}/preroll/clear`, { method: "POST" }),
  generatePreroll: (id) => req(`/api/marathons/${id}/preroll/generate`, { method: "POST" }),

  // NeXroll
  listNexroll: () => req("/api/nexroll"),
  createNexroll: (body) => req("/api/nexroll", { method: "POST", body: JSON.stringify(body) }),
  deleteNexroll: (id) => req(`/api/nexroll/${id}`, { method: "DELETE" }),
  nexrollStatus: (id) => req(`/api/nexroll/${id}/status`),
  nexrollPrerolls: (id) => req(`/api/nexroll/${id}/prerolls`),
};
