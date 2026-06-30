import { useEffect, useState } from "react";
import { KeyRound, Check, Film, Radar, Tv, Plug, CheckCircle2, XCircle, Trash2 } from "lucide-react";
import { Card, Button, Field, Spinner } from "../ui.jsx";
import { api, getApiKey, setApiKey } from "../api.js";

const SOON = [
  { icon: Radar, title: "Radarr", desc: "Auto-request movies missing from a recipe.", phase: "Phase 4" },
  { icon: Tv, title: "Sonarr", desc: "Auto-request series and episodes for gap-fill.", phase: "Phase 4" },
];

export default function Settings() {
  const [keyInput, setKeyInput] = useState(getApiKey());
  const [saved, setSaved] = useState(false);

  function save() {
    setApiKey(keyInput.trim());
    setSaved(true);
    setTimeout(() => setSaved(false), 1800);
  }

  return (
    <div className="grid grid-2">
      <Card title="Access key" sub="Sent as the X-Api-Key header on every request.">
        <p className="muted" style={{ fontSize: 13.5, lineHeight: 1.55, marginBottom: 14 }}>
          Find the generated key in the backend startup log, or pin your own with
          the <span className="mono">BINGEARR_API_KEY</span> environment variable.
          It is stored only in this browser.
        </p>
        <Field label="API key">
          <input
            type="password"
            value={keyInput}
            onChange={(e) => setKeyInput(e.target.value)}
            placeholder="Paste your key"
          />
        </Field>
        <Button icon={saved ? Check : KeyRound} onClick={save}>
          {saved ? "Saved" : "Save key"}
        </Button>
      </Card>

      <div>
        <NeXrollCard />
        <Card title="More integrations" sub="Connect the rest of your stack.">
          {SOON.map(({ icon: Icon, title, desc, phase }) => (
            <div className="integration" key={title}>
              <div className="integration-icon"><Icon size={20} /></div>
              <div className="integration-body">
                <div className="integration-title">{title}</div>
                <div className="integration-desc">{desc}</div>
              </div>
              <span className="soon">{phase}</span>
            </div>
          ))}
        </Card>
      </div>
    </div>
  );
}

function NeXrollCard() {
  const [conn, setConn] = useState(null);
  const [form, setForm] = useState({ base_url: "", api_key: "" });
  const [status, setStatus] = useState(null);
  const [prerolls, setPrerolls] = useState([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  function load() {
    api
      .listNexroll()
      .then((list) => {
        const c = list[0] || null;
        setConn(c);
        if (c) refresh(c.id);
      })
      .catch(() => {});
  }

  function refresh(id) {
    api.nexrollStatus(id).then(setStatus).catch(() => setStatus({ ok: false }));
    api.nexrollPrerolls(id).then(setPrerolls).catch(() => setPrerolls([]));
  }

  useEffect(load, []);

  function connect(e) {
    e.preventDefault();
    setBusy(true);
    setError("");
    api
      .createNexroll(form)
      .then(() => {
        setForm({ base_url: "", api_key: "" });
        load();
      })
      .catch((e) => setError(e.message))
      .finally(() => setBusy(false));
  }

  function disconnect() {
    if (!conn) return;
    api.deleteNexroll(conn.id).then(() => {
      setConn(null);
      setStatus(null);
      setPrerolls([]);
    });
  }

  return (
    <Card
      title="NeXroll"
      sub="Attach prerolls to your marathons."
      action={
        <div className="integration-icon" style={{ width: 34, height: 34 }}>
          <Film size={18} />
        </div>
      }
    >
      {conn ? (
        <>
          <div className="between" style={{ marginBottom: 12 }}>
            <div>
              <div style={{ fontSize: 14 }}>{conn.base_url}</div>
              <div className="mt" style={{ marginTop: 6 }}>
                {status === null ? (
                  <span className="test-line">
                    <Spinner /> checking…
                  </span>
                ) : status.ok ? (
                  <span className="test-line ok">
                    <CheckCircle2 size={14} /> Connected · v{status.version} ·{" "}
                    {prerolls.length} prerolls
                  </span>
                ) : (
                  <span className="test-line bad">
                    <XCircle size={14} /> {status.message || "Unreachable"}
                  </span>
                )}
              </div>
            </div>
            <Button variant="danger" size="sm" icon={Trash2} onClick={disconnect}>
              Disconnect
            </Button>
          </div>
        </>
      ) : (
        <form onSubmit={connect}>
          <Field label="Base URL">
            <input
              value={form.base_url}
              onChange={(e) => setForm({ ...form, base_url: e.target.value })}
              placeholder="http://192.168.1.10:9393"
            />
          </Field>
          <Field label="API key">
            <input
              type="password"
              value={form.api_key}
              onChange={(e) => setForm({ ...form, api_key: e.target.value })}
              placeholder="NeXroll integration key"
            />
          </Field>
          {error && <div className="error" style={{ marginBottom: 10 }}>{error}</div>}
          <Button icon={busy ? undefined : Plug} type="submit" disabled={busy || !form.base_url || !form.api_key}>
            {busy ? <Spinner /> : "Connect"}
          </Button>
        </form>
      )}
    </Card>
  );
}
