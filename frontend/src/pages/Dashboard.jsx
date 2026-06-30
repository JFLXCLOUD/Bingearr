import { useEffect, useState } from "react";
import { Server, Clapperboard, KeyRound, Check, ArrowRight } from "lucide-react";
import { Card, Button, EmptyState } from "../ui.jsx";
import { api, getApiKey } from "../api.js";

export default function Dashboard({ setPage }) {
  const [servers, setServers] = useState([]);
  const [marathons, setMarathons] = useState([]);
  const hasKey = !!getApiKey();

  useEffect(() => {
    if (!hasKey) return;
    api.listServers().then(setServers).catch(() => {});
    api.listMarathons().then(setMarathons).catch(() => {});
  }, [hasKey]);

  if (!hasKey) {
    return (
      <Card>
        <EmptyState
          icon={KeyRound}
          title="Add your access key to begin"
          action={
            <Button icon={ArrowRight} onClick={() => setPage("settings")}>
              Go to Settings
            </Button>
          }
        >
          Bingearr protects its API with a key (printed in the backend log on
          first start). Paste it in Settings to unlock servers and marathons.
        </EmptyState>
      </Card>
    );
  }

  const steps = [
    { done: hasKey, title: "Add your access key", desc: "Authenticate the UI against the Bingearr API." },
    { done: servers.length > 0, title: "Connect a media server", desc: "Point Bingearr at your Plex library." },
    { done: marathons.length > 0, title: "Build your first marathon", desc: "Pick titles, set the order, push to Plex." },
  ];

  return (
    <>
      <div className="grid grid-3">
        <Card>
          <div className="stat">
            <div className="stat-icon"><Server size={22} /></div>
            <div>
              <div className="stat-num">{servers.length}</div>
              <div className="stat-label">Media servers</div>
            </div>
          </div>
        </Card>
        <Card>
          <div className="stat">
            <div className="stat-icon"><Clapperboard size={22} /></div>
            <div>
              <div className="stat-num">{marathons.length}</div>
              <div className="stat-label">Marathons</div>
            </div>
          </div>
        </Card>
        <Card>
          <div className="stat">
            <div className="stat-icon"><KeyRound size={22} /></div>
            <div>
              <div className="stat-num">On</div>
              <div className="stat-label">API authenticated</div>
            </div>
          </div>
        </Card>
      </div>

      <Card title="Getting started" sub="Three steps to your first binge.">
        <div className="steps">
          {steps.map((s, i) => (
            <div key={i} className={`step ${s.done ? "done" : ""}`}>
              <div className="step-check">{s.done && <Check size={15} strokeWidth={3} />}</div>
              <div className="step-body">
                <div className="step-title">{s.title}</div>
                <div className="step-desc">{s.desc}</div>
              </div>
              {!s.done && i === 1 && (
                <Button variant="ghost" size="sm" onClick={() => setPage("servers")}>
                  Connect
                </Button>
              )}
            </div>
          ))}
        </div>
      </Card>
    </>
  );
}
