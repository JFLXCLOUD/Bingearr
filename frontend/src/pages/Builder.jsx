import { useEffect, useState } from "react";
import {
  ArrowLeft,
  Search,
  Plus,
  Check,
  ChevronUp,
  ChevronDown,
  X,
  Save,
  Film,
  ListVideo,
  Layers,
  Sparkles,
} from "lucide-react";
import { Card, Button, Field, EmptyState, Spinner, formatRuntime } from "../ui.jsx";
import { api } from "../api.js";

const PAGE = 50;

export default function Builder({ marathonId, onClose }) {
  const [servers, setServers] = useState([]);
  const [serverId, setServerId] = useState(null);
  const [libraries, setLibraries] = useState([]);
  const [libraryKey, setLibraryKey] = useState(null);
  const [tab, setTab] = useState("titles"); // titles | collections

  const [search, setSearch] = useState("");
  const [results, setResults] = useState([]);
  const [offset, setOffset] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const [loading, setLoading] = useState(false);

  const [collections, setCollections] = useState([]);
  const [unwatchedOnly, setUnwatchedOnly] = useState(false);
  const [busy, setBusy] = useState("");

  const [genres, setGenres] = useState([]);
  const [genre, setGenre] = useState("");
  const [watch, setWatch] = useState("all");
  const [minutes, setMinutes] = useState(240);
  const [generating, setGenerating] = useState(false);

  const [selected, setSelected] = useState([]);
  const [name, setName] = useState("");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  const currentLib = libraries.find((l) => l.key === libraryKey);
  const isShows = currentLib?.type === "show";

  // Servers
  useEffect(() => {
    api
      .listServers()
      .then((s) => {
        setServers(s);
        if (s[0] && !marathonId) setServerId(s[0].id);
      })
      .catch((e) => setError(e.message));
  }, [marathonId]);

  // Existing marathon (edit mode)
  useEffect(() => {
    if (!marathonId) return;
    api
      .getMarathon(marathonId)
      .then((m) => {
        setName(m.name);
        if (m.server_id) setServerId(m.server_id);
        setSelected(
          m.items.map((i) => ({
            server_item_id: i.server_item_id,
            title: i.title,
            runtime_minutes: i.runtime_minutes,
          }))
        );
      })
      .catch((e) => setError(e.message));
  }, [marathonId]);

  // Libraries when the server changes
  useEffect(() => {
    if (!serverId) return;
    setLibraries([]);
    setLibraryKey(null);
    api
      .listLibraries(serverId)
      .then((libs) => {
        setLibraries(libs);
        const first = libs.find((l) => l.type === "movie") || libs[0];
        if (first) setLibraryKey(first.key);
      })
      .catch((e) => setError(e.message));
  }, [serverId]);

  // Titles when the library changes
  useEffect(() => {
    if (serverId && libraryKey && tab === "titles") loadItems(0, true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [serverId, libraryKey, tab]);

  // Collections when switching to that tab
  useEffect(() => {
    if (!(serverId && libraryKey && tab === "collections")) return;
    setCollections([]);
    api
      .listCollections(serverId, libraryKey)
      .then(setCollections)
      .catch((e) => setError(e.message));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [serverId, libraryKey, tab]);

  // Genres when switching to the smart tab
  useEffect(() => {
    if (!(serverId && libraryKey && tab === "smart")) return;
    api.listGenres(serverId, libraryKey).then(setGenres).catch(() => setGenres([]));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [serverId, libraryKey, tab]);

  // Smart mode is movie-oriented; bounce off it for show libraries.
  useEffect(() => {
    if (isShows && tab === "smart") setTab("titles");
  }, [isShows, tab]);

  function loadItems(off, reset) {
    setLoading(true);
    setError("");
    api
      .listItems(serverId, libraryKey, { search: search || undefined, limit: PAGE, offset: off })
      .then((items) => {
        setResults((prev) => (reset ? items : [...prev, ...items]));
        setOffset(off + items.length);
        setHasMore(items.length === PAGE);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }

  function runSearch(e) {
    e.preventDefault();
    loadItems(0, true);
  }

  const selectedIds = new Set(selected.map((s) => s.server_item_id));

  function appendItems(items) {
    setSelected((prev) => {
      const have = new Set(prev.map((s) => s.server_item_id));
      const add = items
        .filter((i) => !have.has(i.id))
        .map((i) => ({
          server_item_id: i.id,
          title: i.title,
          runtime_minutes: i.runtime_minutes,
        }));
      return [...prev, ...add];
    });
  }

  async function addSeries(show) {
    setBusy(show.id);
    setError("");
    try {
      const eps = await api.expandShow(serverId, show.id, {
        unwatched_only: unwatchedOnly || undefined,
      });
      appendItems(eps);
    } catch (e) {
      setError(e.message);
    }
    setBusy("");
  }

  async function addCollection(col) {
    setBusy(col.id);
    setError("");
    try {
      const items = await api.expandCollection(serverId, col.id);
      appendItems(items);
    } catch (e) {
      setError(e.message);
    }
    setBusy("");
  }

  async function generate() {
    setGenerating(true);
    setError("");
    try {
      const items = await api.smartSelect(serverId, libraryKey, {
        genre: genre || undefined,
        watch,
        minutes: minutes || undefined,
      });
      if (items.length === 0) {
        setError("No titles matched — try a wider genre, a different watch state, or a bigger budget.");
      }
      setSelected(
        items.map((i) => ({
          server_item_id: i.id,
          title: i.title,
          runtime_minutes: i.runtime_minutes,
        }))
      );
    } catch (e) {
      setError(e.message);
    }
    setGenerating(false);
  }

  function removeAt(idx) {
    setSelected(selected.filter((_, i) => i !== idx));
  }
  function move(idx, dir) {
    const j = idx + dir;
    if (j < 0 || j >= selected.length) return;
    const copy = [...selected];
    [copy[idx], copy[j]] = [copy[j], copy[idx]];
    setSelected(copy);
  }

  const totalRuntime = selected.reduce((a, s) => a + (s.runtime_minutes || 0), 0);
  const canSave = name.trim() && selected.length > 0 && serverId;

  function save() {
    if (!canSave) return;
    setSaving(true);
    setError("");
    const action = marathonId
      ? api.updateMarathon(marathonId, { name: name.trim(), items: selected })
      : api.createMarathon({
          name: name.trim(),
          server_id: serverId,
          type: "manual",
          target_kind: "playlist",
          items: selected,
        });
    action
      .then(() => onClose(true))
      .catch((e) => {
        setError(e.message);
        setSaving(false);
      });
  }

  return (
    <>
      <div className="builder-head">
        <div className="left">
          <button className="icon-btn" onClick={() => onClose(false)} title="Back">
            <ArrowLeft size={16} />
          </button>
          <input
            className="title-input"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Marathon name…"
          />
        </div>
        <Button icon={saving ? undefined : Save} onClick={save} disabled={!canSave || saving}>
          {saving ? <Spinner /> : marathonId ? "Save changes" : "Save marathon"}
        </Button>
      </div>

      {error && <div className="flash bad">{error}</div>}

      <div className="grid grid-2">
        {/* Browse / rules */}
        <Card title="Library">
          <div className="row" style={{ marginBottom: 12 }}>
            <div>
              <select value={serverId ?? ""} onChange={(e) => setServerId(Number(e.target.value))}>
                {servers.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <select value={libraryKey ?? ""} onChange={(e) => setLibraryKey(e.target.value)}>
                {libraries.map((l) => (
                  <option key={l.key} value={l.key}>
                    {l.title} ({l.item_count ?? "?"})
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="segment">
            <button className={tab === "titles" ? "active" : ""} onClick={() => setTab("titles")}>
              {isShows ? "Series" : "Titles"}
            </button>
            <button
              className={tab === "collections" ? "active" : ""}
              onClick={() => setTab("collections")}
            >
              Collections
            </button>
            {!isShows && (
              <button className={tab === "smart" ? "active" : ""} onClick={() => setTab("smart")}>
                Smart
              </button>
            )}
          </div>

          {tab === "titles" && (
            <>
              {isShows && (
                <label className="check" style={{ marginBottom: 12 }}>
                  <input
                    type="checkbox"
                    checked={unwatchedOnly}
                    onChange={(e) => setUnwatchedOnly(e.target.checked)}
                  />
                  Unwatched episodes only
                </label>
              )}
              <form className="search-row" onSubmit={runSearch}>
                <input
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder={isShows ? "Search shows…" : "Search titles…"}
                />
                <Button variant="ghost" icon={Search} type="submit">
                  Search
                </Button>
              </form>

              <div className="list-scroll">
                {results.length === 0 && !loading ? (
                  <EmptyState icon={Film} title="No titles">
                    Nothing here yet — pick a library or try a different search.
                  </EmptyState>
                ) : (
                  results.map((it) => {
                    const added = selectedIds.has(it.id);
                    return (
                      <div className="browse-row" key={it.id}>
                        <div className="row-main">
                          <div className="row-title">
                            {it.title}
                            {isShows && <span className="row-tag">full series</span>}
                          </div>
                          <div className="row-meta">
                            {[it.year, !isShows && formatRuntime(it.runtime_minutes)]
                              .filter(Boolean)
                              .join(" · ")}
                          </div>
                        </div>
                        {isShows ? (
                          <button
                            className="icon-btn"
                            onClick={() => addSeries(it)}
                            disabled={busy === it.id}
                            title="Add full series in order"
                          >
                            {busy === it.id ? <Spinner /> : <Plus size={16} />}
                          </button>
                        ) : added ? (
                          <span className="added">
                            <Check size={14} /> Added
                          </span>
                        ) : (
                          <button className="icon-btn" onClick={() => appendItems([it])} title="Add">
                            <Plus size={16} />
                          </button>
                        )}
                      </div>
                    );
                  })
                )}
                {loading && (
                  <div className="row-meta" style={{ padding: "12px 4px" }}>
                    <Spinner /> Loading…
                  </div>
                )}
              </div>

              {hasMore && !loading && tab === "titles" && (
                <div style={{ marginTop: 12 }}>
                  <Button variant="subtle" size="sm" onClick={() => loadItems(offset, false)}>
                    Load more
                  </Button>
                </div>
              )}
            </>
          )}

          {tab === "collections" && (
            <div className="list-scroll">
              {collections.length === 0 ? (
                <EmptyState icon={Layers} title="No collections">
                  This library has no Plex collections. Switch back to{" "}
                  {isShows ? "Series" : "Titles"} to add items individually.
                </EmptyState>
              ) : (
                collections.map((c) => (
                  <div className="browse-row" key={c.id}>
                    <div className="row-main">
                      <div className="row-title">{c.title}</div>
                      <div className="row-meta">{c.item_count ?? "?"} items</div>
                    </div>
                    <button
                      className="icon-btn"
                      onClick={() => addCollection(c)}
                      disabled={busy === c.id}
                      title="Add the whole collection"
                    >
                      {busy === c.id ? <Spinner /> : <Plus size={16} />}
                    </button>
                  </div>
                ))
              )}
            </div>
          )}

          {tab === "smart" && (
            <div>
              <Field label="Genre">
                <select value={genre} onChange={(e) => setGenre(e.target.value)}>
                  <option value="">Any genre</option>
                  {genres.map((g) => (
                    <option key={g} value={g}>
                      {g}
                    </option>
                  ))}
                </select>
              </Field>
              <Field label="Watch state">
                <select value={watch} onChange={(e) => setWatch(e.target.value)}>
                  <option value="all">All</option>
                  <option value="unwatched">Unwatched only</option>
                  <option value="in_progress">Continue watching</option>
                </select>
              </Field>
              <Field label="Time budget (minutes)">
                <input
                  type="number"
                  min="30"
                  step="30"
                  value={minutes}
                  onChange={(e) => setMinutes(Number(e.target.value))}
                />
              </Field>
              <Button
                icon={generating ? undefined : Sparkles}
                onClick={generate}
                disabled={generating}
              >
                {generating ? <Spinner /> : "Generate block"}
              </Button>
              <p className="row-meta" style={{ marginTop: 12 }}>
                Packs a randomized set that fits your budget. Generating replaces the
                current order.
              </p>
            </div>
          )}
        </Card>

        {/* Selection */}
        <Card title="Marathon order">
          <div className="builder-summary">
            <span>
              <b>{selected.length}</b> titles
            </span>
            <span>
              <b>{formatRuntime(totalRuntime)}</b> total
            </span>
          </div>

          {selected.length === 0 ? (
            <EmptyState icon={ListVideo} title="Empty">
              Add titles, a full series, or a collection from the left. Reorder
              with the arrows, then save and push to Plex.
            </EmptyState>
          ) : (
            <div className="list-scroll tall">
              {selected.map((s, idx) => (
                <div className="sel-row" key={s.server_item_id}>
                  <span className="idx">{idx + 1}</span>
                  <div className="row-main">
                    <div className="row-title">{s.title}</div>
                    <div className="row-meta">{formatRuntime(s.runtime_minutes)}</div>
                  </div>
                  <div className="sel-actions">
                    <button
                      className="icon-btn"
                      onClick={() => move(idx, -1)}
                      disabled={idx === 0}
                      title="Move up"
                    >
                      <ChevronUp size={16} />
                    </button>
                    <button
                      className="icon-btn"
                      onClick={() => move(idx, 1)}
                      disabled={idx === selected.length - 1}
                      title="Move down"
                    >
                      <ChevronDown size={16} />
                    </button>
                    <button className="icon-btn" onClick={() => removeAt(idx)} title="Remove">
                      <X size={16} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>
    </>
  );
}
