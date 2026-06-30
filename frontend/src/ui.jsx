import { Loader2 } from "lucide-react";

export function StatusPill({ health }) {
  const ok = !!health;
  return (
    <div className={`pill ${ok ? "pill-ok" : "pill-bad"}`}>
      <span className="pill-dot" />
      {ok ? `Connected · v${health.version}` : "Backend offline"}
    </div>
  );
}

export function Card({ title, sub, action, children, className = "" }) {
  return (
    <section className={`card ${className}`}>
      {(title || action) && (
        <div className="card-head">
          <div>
            {title && <h2>{title}</h2>}
            {sub && <div className="card-sub">{sub}</div>}
          </div>
          {action}
        </div>
      )}
      {children}
    </section>
  );
}

export function Button({ children, variant = "primary", size, icon: Icon, ...props }) {
  return (
    <button className={`btn btn-${variant}${size ? ` btn-${size}` : ""}`} {...props}>
      {Icon && <Icon size={16} strokeWidth={2.2} />}
      {children}
    </button>
  );
}

export function Field({ label, children }) {
  return (
    <label className="field">
      <span>{label}</span>
      {children}
    </label>
  );
}

export function EmptyState({ icon: Icon, title, children, action }) {
  return (
    <div className="empty">
      {Icon && (
        <div className="empty-icon">
          <Icon size={28} strokeWidth={1.6} />
        </div>
      )}
      <h3>{title}</h3>
      {children && <p>{children}</p>}
      {action}
    </div>
  );
}

export function Spinner() {
  return <Loader2 size={15} className="spin" />;
}

export function isAuthError(message = "") {
  return message.startsWith("401") || message.startsWith("403");
}
