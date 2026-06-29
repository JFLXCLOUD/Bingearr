import { useEffect, useState } from "react";
import { api, getApiKey, setApiKey } from "./api.js";

export default function App() {
  const [page, setPage] = useState("dashboard");
  const [health, setHealth] = useState(null);
  const [keyInput, setKeyInput] = useState(getApiKey());

  useEffect(() => {
    api.health().then(setHealth).catch(() => setHealth(null));
  }, []);

  function saveKey() {
    setApiKey(keyInput.trim());
    // Re-render children that depend on the key.
    setPage((p) => p);
  }

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          Binge<span>arr</span>
        </div>
        <div className="tagline">Binge-experience builder</div>
        <nav className="nav">
          {[
            ["dashboard", "Dashboard"],
            ["servers", "Servers"],
            ["marathons", "Marathons"],
          ].map(([id, label]) => (
            <button
              key={id}
              className={page === id ? "active" : ""}
              onClick={() => setPage(id)}
            >
              {label}
            </button>
          ))}
        </nav>
      </aside>

      <main className="main">
        <div className="topbar">
          <h1>{titleFor(page)}</h1>
          <div className="muted">
            <span className={`dot ${health ? "ok" : "bad"}`} />
            {health ? `API ${health.version}` : "API offline"}
          </div>
        </div>

        {page === "dashboard" && (
          <Dashboard
            health={health}
            keyInput={keyInput}
            setKeyInput={setKeyInput}
            saveKey={saveKey}
          />
        )}
        {page === "servers" && <Servers />}
        {page === "marathons" && <Marathons />}
      </main>
    </div>
  );
}

function titleFor(page) {
  return { dashboard: "Dashboard", servers: "Servers", marathons: "Marathons" }[page];
}

function Dashboard({ health, keyInput, setKeyInput, saveKey }) {
  return (
    <>
      <div className="card">
        <h2>Status</h2>
        <p className="muted">
          {health
            ? `Connected to Bingearr ${health.version}.`
            : "Cannot reach the backend. Is uvicorn running on :9494?"}
        </p>
      </div>
      <div className="card">
        <h2>API key</h2>
        <p className="muted">
          Stored in your browser and sent as <code>X-Api-Key</code>. Find the
          generated key in the backend startup log.
        </p>
        <div className="row">
          <div>
            <input
              type="password"
              value={keyInput}
              onChange={(e) => setKeyInput(e.target.value)}
              placeholder="Paste API key"
            />
          </div>
          <button className="primary" onClick={saveKey}>
            Save
          </button>
        </div>
      </div>
    </>
  );
}

function Servers() {
  const [servers, setServers] = useState([]);
  const [error, setError] = useState("");
  const [form, setForm] = useState({
    type: "plex",
    name: "",
    base_url: "",
    token: "",
  });
  const [testResult, setTestResult] = useState(null);

  function load() {
    api
      .listServers()
      .then(setServers)
      .catch((e) => setError(e.message));
  }

  useEffect(load, []);

  function create(e) {
    e.preventDefault();
    setError("");
    api
      .createServer(form)
      .then(() => {
        setForm({ type: "plex", name: "", base_url: "", token: "" });
        load();
      })
      .catch((e) => setError(e.message));
  }

  function test(id) {
    setTestResult({ id, loading: true });
    api
      .testServer(id)
      .then((r) => setTestResult({ id, ...r }))
      .catch((e) => setTestResult({ id, ok: false, message: e.message }));
  }

  function remove(id) {
    api.deleteServer(id).then(load).catch((e) => setError(e.message));
  }

  return (
    <>
      {error && <div className="card error">{error}</div>}

      <div className="card">
        <h2>Add a server</h2>
        <form onSubmit={create}>
          <div className="row">
            <div>
              <label>Type</label>
              <select
                value={form.type}
                onChange={(e) => setForm({ ...form, type: e.target.value })}
              >
                <option value="plex">Plex</option>
                <option value="jellyfin">Jellyfin (soon)</option>
              </select>
            </div>
            <div>
              <label>Name</label>
              <input
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                placeholder="Living Room Plex"
              />
            </div>
          </div>
          <label>Base URL</label>
          <input
            value={form.base_url}
            onChange={(e) => setForm({ ...form, base_url: e.target.value })}
            placeholder="http://192.168.1.10:32400"
          />
          <label>Token</label>
          <input
            type="password"
            value={form.token}
            onChange={(e) => setForm({ ...form, token: e.target.value })}
            placeholder="Plex token"
          />
          <div style={{ marginTop: 14 }}>
            <button className="primary" type="submit">
              Add server
            </button>
          </div>
        </form>
      </div>

      <div className="card">
        <h2>Servers</h2>
        {servers.length === 0 ? (
          <p className="muted">No servers yet.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Type</th>
                <th>URL</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {servers.map((s) => (
                <tr key={s.id}>
                  <td>{s.name}</td>
                  <td>{s.type}</td>
                  <td className="muted">{s.base_url}</td>
                  <td style={{ textAlign: "right", whiteSpace: "nowrap" }}>
                    <button className="ghost" onClick={() => test(s.id)}>
                      Test
                    </button>{" "}
                    <button className="ghost" onClick={() => remove(s.id)}>
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        {testResult && (
          <div style={{ marginTop: 14 }} className="muted">
            {testResult.loading
              ? "Testing…"
              : testResult.ok
              ? `✓ ${testResult.name} (${testResult.version}) — ${
                  testResult.libraries?.length ?? 0
                } libraries`
              : `✗ ${testResult.message}`}
          </div>
        )}
      </div>
    </>
  );
}

function Marathons() {
  const [marathons, setMarathons] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .listMarathons()
      .then(setMarathons)
      .catch((e) => setError(e.message));
  }, []);

  return (
    <div className="card">
      <h2>Marathons</h2>
      {error && <div className="error">{error}</div>}
      {marathons.length === 0 ? (
        <p className="muted">
          No marathons yet. The builder lands in Phase 1 — manual picker plus
          franchise/series ordering, pushed to Plex as a native playlist.
        </p>
      ) : (
        <ul>
          {marathons.map((m) => (
            <li key={m.id}>{m.name}</li>
          ))}
        </ul>
      )}
    </div>
  );
}
