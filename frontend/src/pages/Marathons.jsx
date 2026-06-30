import { useEffect, useState } from "react";
import { Clapperboard, Plus, KeyRound, ArrowRight } from "lucide-react";
import { Card, Button, EmptyState, isAuthError } from "../ui.jsx";
import { api, getApiKey } from "../api.js";

export default function Marathons({ setPage }) {
  const [marathons, setMarathons] = useState([]);
  const [authMissing, setAuthMissing] = useState(!getApiKey());

  useEffect(() => {
    api
      .listMarathons()
      .then((m) => {
        setMarathons(m);
        setAuthMissing(false);
      })
      .catch((e) => {
        if (isAuthError(e.message)) setAuthMissing(true);
      });
  }, []);

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

  return (
    <Card
      title="Marathons"
      sub="Manual picks and franchise/series order, pushed to Plex as a native playlist."
      action={
        <Button icon={Plus} disabled title="Arrives in Phase 1">
          New marathon
        </Button>
      }
    >
      {marathons.length === 0 ? (
        <EmptyState icon={Clapperboard} title="No marathons yet">
          The marathon builder lands in Phase 1: browse a connected library, pick
          and order titles (or let a franchise/series rule do it), then push the
          result to Plex as a native playlist that shows up in every client.
        </EmptyState>
      ) : (
        <table className="table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Type</th>
              <th>Target</th>
            </tr>
          </thead>
          <tbody>
            {marathons.map((m) => (
              <tr key={m.id}>
                <td>{m.name}</td>
                <td><span className="badge">{m.type}</span></td>
                <td className="muted">{m.target_kind}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </Card>
  );
}
