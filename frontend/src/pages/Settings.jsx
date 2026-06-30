import { useState } from "react";
import { KeyRound, Check, Film, Radar, Tv } from "lucide-react";
import { Card, Button, Field } from "../ui.jsx";
import { getApiKey, setApiKey } from "../api.js";

const INTEGRATIONS = [
  { icon: Film, title: "NeXroll", desc: "Attach a preroll that plays before a marathon.", phase: "Phase 3" },
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

      <Card title="Ecosystem integrations" sub="Connect the rest of your stack.">
        {INTEGRATIONS.map(({ icon: Icon, title, desc, phase }) => (
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
  );
}
