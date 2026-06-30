import { useEffect, useState } from "react";
import Sidebar from "./components/Sidebar.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Servers from "./pages/Servers.jsx";
import Marathons from "./pages/Marathons.jsx";
import Settings from "./pages/Settings.jsx";
import { StatusPill } from "./ui.jsx";
import { api } from "./api.js";

const PAGES = {
  dashboard: { title: "Dashboard", subtitle: "Your binge command center", Component: Dashboard },
  servers: { title: "Media Servers", subtitle: "Connect Plex and Jellyfin libraries", Component: Servers },
  marathons: { title: "Marathons", subtitle: "Curated binge experiences, pushed to your server", Component: Marathons },
  settings: { title: "Settings", subtitle: "Access key and ecosystem integrations", Component: Settings },
};

function pageFromHash() {
  const id = window.location.hash.replace(/^#\/?/, "");
  return PAGES[id] ? id : "dashboard";
}

export default function App() {
  const [page, setPageState] = useState(pageFromHash);
  const [health, setHealth] = useState(null);

  const setPage = (id) => {
    window.location.hash = id;
  };

  useEffect(() => {
    const onHash = () => setPageState(pageFromHash());
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);

  useEffect(() => {
    let alive = true;
    const ping = () =>
      api
        .health()
        .then((h) => alive && setHealth(h))
        .catch(() => alive && setHealth(null));
    ping();
    const t = setInterval(ping, 10000);
    return () => {
      alive = false;
      clearInterval(t);
    };
  }, []);

  const { title, subtitle, Component } = PAGES[page];

  return (
    <div className="app">
      <Sidebar page={page} setPage={setPage} health={health} />
      <main className="main">
        <header className="topbar">
          <div>
            <h1>{title}</h1>
            <p className="subtitle">{subtitle}</p>
          </div>
          <StatusPill health={health} />
        </header>
        <div key={page} className="page">
          <Component setPage={setPage} />
        </div>
      </main>
    </div>
  );
}
