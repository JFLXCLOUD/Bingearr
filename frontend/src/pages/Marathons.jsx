import { useEffect, useState } from "react";
import {
  Clapperboard,
  Plus,
  KeyRound,
  ArrowRight,
  Trash2,
  UploadCloud,
  Pencil,
  CheckCircle2,
} from "lucide-react";
import { Card, Button, EmptyState, Spinner, isAuthError, formatRuntime } from "../ui.jsx";
import { api, getApiKey } from "../api.js";
import Builder from "./Builder.jsx";

export default function Marathons({ setPage }) {
  const [view, setView] = useState({ mode: "list" });
  const [marathons, setMarathons] = useState([]);
  const [authMissing, setAuthMissing] = useState(!getApiKey());
  const [pushing, setPushing] = useState({});
  const [flash, setFlash] = useState(null);

  function load() {
    api
      .listMarathons()
      .then((m) => {
        setMarathons(m);
        setAuthMissing(false);
      })
      .catch((e) => {
        if (isAuthError(e.message)) setAuthMissing(true);
      });
  }

  useEffect(load, []);

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
          Add your API key in Settings to view and build marathons.
        </EmptyState>
      </Card>
    );
  }

  if (view.mode === "builder") {
    return (
      <Builder
        marathonId={view.id}
        onClose={(saved) => {
          setView({ mode: "list" });
          if (saved) {
            setFlash({ ok: true, msg: "Marathon saved. Push it to Plex when you're ready." });
            load();
          }
        }}
      />
    );
  }

  function push(id) {
    setPushing((p) => ({ ...p, [id]: true }));
    setFlash(null);
    api
      .pushMarathon(id)
      .then((r) => {
        setFlash({
          ok: true,
          msg: `Pushed ${r.item_count} titles to Plex as a playlist. Open Plex to watch — it shows up in every client.`,
        });
        load();
      })
      .catch((e) => setFlash({ ok: false, msg: e.message }))
      .finally(() => setPushing((p) => ({ ...p, [id]: false })));
  }

  function remove(id) {
    api.deleteMarathon(id).then(load).catch((e) => setFlash({ ok: false, msg: e.message }));
  }

  return (
    <Card
      title="Marathons"
      sub="Manual picks, pushed to Plex as a native playlist."
      action={
        <Button icon={Plus} onClick={() => setView({ mode: "builder" })}>
          New marathon
        </Button>
      }
    >
      {flash && <div className={`flash ${flash.ok ? "ok" : "bad"}`}>{flash.msg}</div>}

      {marathons.length === 0 ? (
        <EmptyState icon={Clapperboard} title="No marathons yet">
          Build your first one: browse a connected library, pick and order titles,
          then push the result to Plex as a native playlist that shows up in every
          client.
        </EmptyState>
      ) : (
        <table className="table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Titles</th>
              <th>Runtime</th>
              <th>Status</th>
              <th className="right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {marathons.map((m) => (
              <tr key={m.id}>
                <td>{m.name}</td>
                <td>{m.item_count}</td>
                <td className="muted">{formatRuntime(m.total_runtime_minutes)}</td>
                <td>
                  {m.server_playlist_id ? (
                    <span className="test-line ok">
                      <CheckCircle2 size={14} /> On Plex
                    </span>
                  ) : (
                    <span className="badge">Draft</span>
                  )}
                </td>
                <td className="right">
                  <Button
                    variant="ghost"
                    size="sm"
                    icon={Pencil}
                    onClick={() => setView({ mode: "builder", id: m.id })}
                  >
                    Edit
                  </Button>{" "}
                  <Button
                    variant="primary"
                    size="sm"
                    icon={pushing[m.id] ? undefined : UploadCloud}
                    onClick={() => push(m.id)}
                    disabled={pushing[m.id] || m.item_count === 0}
                  >
                    {pushing[m.id] ? <Spinner /> : m.server_playlist_id ? "Re-push" : "Push to Plex"}
                  </Button>{" "}
                  <Button
                    variant="danger"
                    size="sm"
                    icon={Trash2}
                    onClick={() => remove(m.id)}
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </Card>
  );
}
