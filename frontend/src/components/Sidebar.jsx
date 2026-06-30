import { LayoutDashboard, Server, Clapperboard, Settings } from "lucide-react";
import Logo from "./Logo.jsx";

const NAV = [
  { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
  { id: "servers", label: "Servers", icon: Server },
  { id: "marathons", label: "Marathons", icon: Clapperboard },
  { id: "settings", label: "Settings", icon: Settings },
];

export default function Sidebar({ page, setPage, health }) {
  return (
    <aside className="sidebar">
      <Logo />
      <nav className="nav">
        <div className="nav-label">Menu</div>
        {NAV.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            className={`nav-item ${page === id ? "active" : ""}`}
            onClick={() => setPage(id)}
          >
            <Icon size={18} strokeWidth={2} />
            <span>{label}</span>
          </button>
        ))}
      </nav>
      <div className="sidebar-foot">
        <div className={`health ${health ? "ok" : "bad"}`}>
          <span className="health-dot" />
          {health ? "All systems go" : "Backend offline"}
        </div>
      </div>
    </aside>
  );
}
