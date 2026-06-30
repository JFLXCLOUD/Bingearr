import { useEffect, useState } from "react";
import {
  Plus,
  Trash2,
  Plug,
  CheckCircle2,
  XCircle,
  KeyRound,
  ArrowRight,
} from "lucide-react";
import { Card, Button, Field, EmptyState, Spinner, isAuthError } from "../ui.jsx";
import { api, getApiKey } from "../api.js";

const BLANK = { type: "plex", name: "", base_url: "", token: "" };

export default function Servers({ setPage }) {
  const [servers, setServers] = useState([]);
  const [form, setForm] = useState(BLANK);
  const [error, setError] = useState("");
  const [results, setResults] = useState({});
  const [authMissing, setAuthMissing] = useState(!getApiKey());

  function load() {
    api
      .listServers()
      .then((s) => {
        setServers(s);
        setAuthMissing(false);
        setError("");
      })
      .catch((e) => {
        if (isAuthError(e.message)) setAuthMissing(true);
        else setError(e.message);
      });
  }

  useEffect(load, []);

  function create(e) {
    e.preventDefault();
    setError("");
    api
      .createServer(form)
      .then(() => {
        setForm(BLANK);
        load();
      })
      .catch((e) => setError(e.message));
  }

  function test(id) {
    setResults((r) => ({ ...r, [id]: { loading: true } }));
    api
      .testServer(id)
      .then((res) => setResults((r) => ({ ...r, [id]: res })))
      .catch((e) => setResults((r) => ({ ...r, [id]: { ok: false, message: e.message } })));
  }

  function remove(id) {
    api.deleteServer(id).then(load).catch((e) => setError(e.message));
  }

  if (authMissing) {
    return (
      <Card>
        <EmptyState
          icon={KeyRound}
          title="Access key required"
          action={
            <Button icon={ArrowRight} onClick={() => setPage("settings")}>
              Open Settings
            </Button>
          }
        >
          Add your API key in Settings before connecting a media server.
        </EmptyState>
      </Card>
    );
  }

  return (
    <div className="grid grid-2">
      <div>
        <Card title="Add a server" sub="Plex now; Jellyfin is on the way.">
          <form onSubmit={create}>
            <div className="row">
              <Field label="Type">
                <select value={form.type} onChange={(e) => setForm({ ...form, type: e.target.value })}>
                  <option value="plex">Plex</option>
                  <option value="jellyfin">Jellyfin</option>
                </select>
              </Field>
              <Field label="Name">
                <input
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  placeholder="Living Room Plex"
                />
              </Field>
            </div>
            <Field label="Base URL">
              <input
                value={form.base_url}
                onChange={(e) => setForm({ ...form, base_url: e.target.value })}
                placeholder="http://192.168.1.10:32400"
              />
            </Field>
            <Field label="Token">
              <input
                type="password"
                value={form.token}
                onChange={(e) => setForm({ ...form, token: e.target.value })}
                placeholder="Plex token"
              />
            </Field>
            {error && <div className="error mt">{error}</div>}
            <div className="mt">
              <Button icon={Plus} type="submit" disabled={!form.name || !form.base_url || !form.token}>
                Add server
              </Button>
            </div>
          </form>
        </Card>
      </div>

      <div>
        <Card title="Connected servers">
          {servers.length === 0 ? (
            <EmptyState icon={Plug} title="No servers yet">
              Add a Plex server on the left, then test the connection to list its
              libraries.
            </EmptyState>
          ) : (
            <table className="table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Type</th>
                  <th className="right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {servers.map((s) => {
                  const r = results[s.id];
                  return (
                    <tr key={s.id}>
                      <td>
                        <div>{s.name}</div>
                        <div className="muted mono">{s.base_url}</div>
                        {r && !r.loading && (
                          <div className={`test-line ${r.ok ? "ok" : "bad"} mt`} style={{ marginTop: 6 }}>
                            {r.ok ? <CheckCircle2 size={14} /> : <XCircle size={14} />}
                            {r.ok
                              ? `${r.name} · ${r.libraries?.length ?? 0} libraries`
                              : r.message}
                          </div>
                        )}
                        {r?.loading && (
                          <div className="test-line mt" style={{ marginTop: 6 }}>
                            <Spinner /> Testing…
                          </div>
                        )}
                      </td>
                      <td>
                        <span className={`badge ${s.type}`}>{s.type}</span>
                      </td>
                      <td className="right">
                        <Button variant="ghost" size="sm" icon={Plug} onClick={() => test(s.id)}>
                          Test
                        </Button>{" "}
                        <Button variant="danger" size="sm" icon={Trash2} onClick={() => remove(s.id)} />
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </Card>
      </div>
    </div>
  );
}
