import { useAuth } from "@clerk/react";
import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import WorldMemory from '../components/WorldMemory';
import { getNeuralStatus, getWorldGraph, getWorldMemory, reviewMemoryItem, searchMemory, queueBackfill } from "../services/api";

export default function MemoryPage() {
  const { getToken } = useAuth();
  return <MemoryWorkspace getToken={getToken}/>;
}

export function MemoryWorkspace({getToken}) {
  const [query, setQuery] = useState("");
  const [result, setResult] = useState(null);
  const [memory, setMemory] = useState(null);
  const [graph, setGraph] = useState(null);
  const [status, setStatus] = useState(null);
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(true);
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState("");

  async function load() {
    setLoading(true);
    try {
      const token = await getToken();
      const [nextMemory, nextGraph, nextStatus] = await Promise.all([getWorldMemory(token), getWorldGraph(token), getNeuralStatus(token)]);
      setMemory(nextMemory);
      setGraph(nextGraph);
      setStatus(nextStatus);
    } catch (nextError) {
      setError(nextError.message || "Unable to load memory.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, [getToken]);

  async function submit(event) {
    event.preventDefault();
    if (!query.trim()) return;
    setSearching(true);
    setError("");
    try { setResult(await searchMemory(query.trim(), await getToken(), 6)); }
    catch (nextError) { setError(nextError.message || "Memory search failed."); }
    finally { setSearching(false); }
  }

  async function review(item, nextStatus) {
    try {
      await reviewMemoryItem(item.id, nextStatus, memory.revision, await getToken());
      await load();
    } catch (nextError) { setError(nextError.message); }
  }

  const node = useMemo(() => graph?.nodes?.find((item) => item.id === selected), [graph, selected]);
  const edges = useMemo(() => graph?.edges?.filter((edge) => edge.source === selected || edge.target === selected) || [], [graph, selected]);

  return <section className="memory-workspace">
    <header className="workspace-header">
      <div><p className="eyebrow">Local, user-owned evidence</p><h1>Memory workspace</h1><p className="muted">Search committed conversation scenes and inspect how scenes, entities, and threads connect.</p></div>
      <Link className="ghost-btn inline-link" to="/settings">Privacy settings</Link>
    </header>
    {error && <p className="error-text" role="alert">{error}</p>}
    <div className="memory-status-strip">
      <span>Index: {typeof status?.embedding === 'string' ? status.embedding : status?.embedding?.status || "loading"}</span>
      <span>Coverage: {status?.coverage?.indexed_scenes ?? "—"} / {status?.coverage?.active_scenes ?? "—"} active scenes</span>
      <span>Revision: {memory?.revision ?? "—"}</span>
    </div>
    <div className="memory-grid">
      <aside className="memory-rail">
        <form className="stack-form" onSubmit={submit}>
          <label htmlFor="memory-query">Search your conversation memory</label>
          <textarea id="memory-query" rows="4" maxLength="2000" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Describe a thought, event, person, or phrase…" />
          <button className="primary-btn" disabled={searching || !query.trim()}>{searching ? "Searching…" : "Search local memory"}</button>
        </form>
        <h2>Threads</h2>
        {memory?.threads?.length ? memory.threads.map((thread) => <button className="filter-chip" key={thread.id} onClick={() => {setResult({status:'ready',method:'thread',results:(memory.scenes||[]).filter(s=>s.thread_id===thread.id).map(s=>({...s,scene_id:s.id,excerpt:s.text,source_session_id:s.session_id,source_turn_id:s.turn_id}))});}}>{thread.id} · {thread.count} turns</button>) : <p className="muted">Threads appear after eligible turns are committed.</p>}
        <h2>Unresolved references</h2>
        {memory?.unresolved?.length ? memory.unresolved.map((item) => <article className="review-card" key={item.id}><p>{item.type} · {item.status}</p><div><button onClick={() => review(item, "acknowledged")}>Acknowledge</button><button onClick={() => review(item, "dismissed")}>Dismiss</button></div></article>) : <p className="muted">Nothing needs review.</p>}
      </aside>
      <main className="memory-results" aria-live="polite">
        <h2>Matching scenes</h2>
        {!result && <p className="empty-state">Search is local. Historical excerpts are never sent to the response provider unless you explicitly enable sharing.</p>}
        {result && <><p className="muted">{result.status} · {result.method} · indexed {result.coverage?.indexed_scenes} / {result.coverage?.eligible_scenes}. Results are exploratory matches, not verified relevance.</p>
          {result.results?.length ? result.results.map((scene) => <article className="memory-result" key={`${scene.scene_id}:${scene.source_turn_id}`}><div className="result-heading"><p className="eyebrow">Scene {scene.scene_id}</p><button className="text-btn" onClick={() => setSelected(scene.scene_id)}>View connections</button></div><blockquote>{scene.excerpt}</blockquote><p><strong>Match:</strong> “{scene.query_excerpt || query}”</p><div className="score-row"><span>Lexical {scene.lexical_score ?? "—"}</span><span>Semantic {scene.semantic_score ?? "—"}</span><span>RRF {scene.fusion_score}</span></div><Link to={`/analysis?session_id=${encodeURIComponent(scene.source_session_id)}&turn_id=${scene.source_turn_id}`}>Open source turn</Link></article>) : <p className="empty-state">No matching committed scenes were found.</p>}</>}
      </main>
      <aside className="memory-context">
        <h2>Connections</h2>
        {loading ? <p className="muted">Loading memory graph…</p> : null}
        {!selected && <p className="muted">Select a result or graph node to inspect direct connections.</p>}
        {node && <article className="evidence-card"><p className="eyebrow">{node.type}</p><h3>{node.label}</h3>{node.text && <p>{node.text}</p>}<ul>{edges.map((edge, index) => <li key={index}>{edge.type} · evidence {(edge.evidence_scene_ids || [edge.evidence_scene_id]).join(", ")}</li>)}</ul></article>}
        <div className="graph-list">{graph?.nodes?.map((item) => <button key={item.id} className={selected === item.id ? "graph-node selected" : "graph-node"} onClick={() => setSelected(item.id)}>{item.label || item.id}</button>)}</div>
      </aside>
    </div>
    <WorldMemory memory={memory} graph={graph} onReview={(id,next)=>review({id},next)}/>
  </section>;
}
