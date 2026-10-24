import { Link } from "react-router-dom";

export default function DashboardPage() {
  return (
    <section className="page-panel dashboard-panel">
      <h1>Your reflection dashboard</h1>
      <p className="muted">Start a reflective conversation, capture journal snapshots, or review qualitative insights.</p>
      <div className="card-grid">
        <article className="card">
          <h3>Reflect now</h3>
          <p>Enter chat and continue your narrative with policy-safe reflection.</p>
          <Link to="/chat" className="inline-link primary-btn small-btn">
            Open Chat
          </Link>
        </article>
        <article className="card">
          <h3>Memory workspace</h3>
          <p>Search local conversation scenes, inspect matching evidence, and review connected threads.</p>
          <Link to="/memory" className="inline-link ghost-btn small-btn">Open Memory</Link>
        </article>
        <article className="card">
          <h3>Journal snapshots</h3>
          <p>Save key conversation turns with your own notes and keep them editable.</p>
          <Link to="/journal" className="inline-link ghost-btn small-btn">
            Open Journal
          </Link>
        </article>
        <article className="card">
          <h3>Insights</h3>
          <p>See non-gamified qualitative summaries from your saved journal entries.</p>
          <Link to="/insights" className="inline-link ghost-btn small-btn">
            Open Insights
          </Link>
        </article>
        <article className="card">
          <h3>Emergency resources</h3>
          <p>Always available, no login required, with hotline and grounding links.</p>
          <Link to="/emergency" className="inline-link ghost-btn small-btn">
            Open Emergency Page
          </Link>
        </article>
      </div>
    </section>
  );
}
