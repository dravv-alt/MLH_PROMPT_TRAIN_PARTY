import { Link } from "react-router-dom";
import NeuralTools from "./NeuralTools";

const featureNames = {
  entity_continuity: "Entity continuity",
  connective_density: "Connective density",
  hedge_density: "Hedge density",
  topic_novelty: "Topic novelty",
};

function score(value) {
  return value == null ? "Unavailable" : Number(value).toFixed(2);
}

export default function TurnInsightDrawer({ analysis, getToken, onClose }) {
  if (!analysis) return null;
  const retrieval = analysis.semantic_retrieval;
  const classification = analysis.classification;

  return (
    <aside className="turn-drawer" aria-label="Turn insights">
      <header className="drawer-header">
        <div>
          <p className="eyebrow">Committed turn evidence</p>
          <h2>Turn insights</h2>
        </div>
        <button className="text-btn" type="button" onClick={onClose} aria-label="Close turn insights">Close</button>
      </header>

      <section className="drawer-summary">
        <p><strong>{analysis.topic_id ? "Topic continued" : "No stable topic yet"}</strong></p>
        <p className="muted">Strategy: {analysis.strategy}. This is textual analysis, not a diagnosis.</p>
        <div className="signal-row">
          {Object.entries(featureNames).map(([key, label]) => (
            <span key={key}><strong>{label}</strong> {score(analysis.features?.[key])}</span>
          ))}
        </div>
      </section>

      <details open>
        <summary>Related memory</summary>
        {retrieval?.results?.length ? (
          <div className="drawer-list">
            {retrieval.results.slice(0, 3).map((result) => (
              <article key={`${result.scene_id}:${result.source_turn_id}`} className="evidence-card">
                <p className="eyebrow">RRF {result.fusion_score}</p>
                <blockquote>{result.excerpt}</blockquote>
                <p className="muted">Lexical {result.lexical_score ?? "—"} · semantic {result.semantic_score ?? "—"}</p>
                <Link to={`/analysis?session_id=${encodeURIComponent(result.source_session_id)}&turn_id=${result.source_turn_id}`}>Open source turn</Link>
              </article>
            ))}
          </div>
        ) : <p className="muted">No earlier local memory match is available for this turn.</p>}
        <Link className="inline-link ghost-btn small-btn" to="/memory">Explore all memory</Link>
      </details>

      <details>
        <summary>Language structure</summary>
        <p>{analysis.clauses?.length || 0} clauses · {analysis.relations?.length || 0} accepted explicit connective relations.</p>
        {analysis.relations?.length ? <ul>{analysis.relations.map((relation) => <li key={relation.id}>{relation.cue}: {relation.relation}</li>)}</ul> : <p className="muted">No supported explicit connective was found. This is a valid result.</p>}
        <Link to="/analysis" state={{ focus: "structure" }}>Open Analysis Studio</Link>
      </details>

      <details>
        <summary>Experimental suggestions</summary>
        <p className="muted">{classification?.status === "pending" ? "Suggestions are being prepared locally." : "Experimental, not validated on Sanctuary conversations."}</p>
        <NeuralTools analysis={analysis} getToken={getToken} compact />
      </details>
    </aside>
  );
}
