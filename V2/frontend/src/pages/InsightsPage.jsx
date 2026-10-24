import { useAuth } from "@clerk/react";
import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { listJournalEntries } from "../services/api";

function formatTimestamp(isoValue) {
  const parsed = Date.parse(isoValue);
  if (Number.isNaN(parsed)) {
    return "Unknown time";
  }
  return new Date(parsed).toLocaleString();
}

export default function InsightsPage() {
  const { getToken } = useAuth();
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let isActive = true;

    async function loadEntries() {
      setLoading(true);
      try {
        const token = await getToken();
        if (!token) {
          throw new Error("Authentication token not available. Please sign in again.");
        }

        const response = await listJournalEntries(token);
        if (isActive) {
          setEntries(response.entries || []);
        }
      } catch (apiError) {
        if (isActive) {
          setError(apiError.message || "Unable to load insights.");
        }
      } finally {
        if (isActive) {
          setLoading(false);
        }
      }
    }

    loadEntries();

    return () => {
      isActive = false;
    };
  }, [getToken]);

  const metrics = useMemo(() => {
    const totalEntries = entries.length;
    const uniqueSessions = new Set(entries.map((entry) => entry.session_id)).size;
    const totalSelectedTurns = entries.reduce((accumulator, entry) => accumulator + (entry.selected_turn_ids?.length || 0), 0);
    const averageTurnsPerEntry = totalEntries ? (totalSelectedTurns / totalEntries).toFixed(1) : "0.0";

    const labelCounts = {};
    entries.forEach((entry) => {
      (entry.reasoning_labels || []).forEach((label) => {
        labelCounts[label] = (labelCounts[label] || 0) + 1;
      });
    });

    const topLabels = Object.entries(labelCounts)
      .sort((left, right) => right[1] - left[1])
      .slice(0, 6)
      .map(([label, count]) => ({ label, count }));

    const latestUpdated = [...entries]
      .sort((left, right) => Date.parse(right.updated_at) - Date.parse(left.updated_at))
      .slice(0, 5);

    return {
      totalEntries,
      uniqueSessions,
      averageTurnsPerEntry,
      topLabels,
      latestUpdated,
    };
  }, [entries]);

  return (
    <section className="page-panel insights-panel">
      <div className="chat-header">
        <h1>Insights</h1>
        <Link to="/journal" className="ghost-btn inline-link">
          Open Journal
        </Link>
      </div>
      <p className="muted">
        These summaries stay qualitative and non-gamified. They are meant to support reflection, not score your emotional life.
      </p>

      {error ? <p className="error-text">{error}</p> : null}
      {loading ? <p className="muted">Loading insights...</p> : null}

      <div className="card-grid">
        <article className="card">
          <p className="eyebrow">Journal entries</p>
          <h3>{metrics.totalEntries}</h3>
          <p className="muted">Saved reflections across all sessions.</p>
        </article>
        <article className="card">
          <p className="eyebrow">Sessions represented</p>
          <h3>{metrics.uniqueSessions}</h3>
          <p className="muted">Distinct conversation sessions linked to entries.</p>
        </article>
        <article className="card">
          <p className="eyebrow">Average selected turns</p>
          <h3>{metrics.averageTurnsPerEntry}</h3>
          <p className="muted">Turn references per journal entry.</p>
        </article>
      </div>

      <div className="split-grid">
        <article className="card">
          <h3>Most common reasoning labels</h3>
          {metrics.topLabels.length === 0 ? (
            <p className="muted">No labels available yet. Create journal entries to see patterns.</p>
          ) : (
            <ul className="insight-list">
              {metrics.topLabels.map((item) => (
                <li key={item.label}>
                  <strong>{item.label}</strong>
                  <span>{item.count}</span>
                </li>
              ))}
            </ul>
          )}
        </article>

        <article className="card">
          <h3>Recently updated entries</h3>
          {metrics.latestUpdated.length === 0 ? (
            <p className="muted">No entries yet.</p>
          ) : (
            <ul className="recent-list">
              {metrics.latestUpdated.map((entry) => (
                <li key={entry.entry_id}>
                  <p>
                    <strong>{entry.entry_title || "Untitled reflection"}</strong>
                  </p>
                  <p className="muted">Session {entry.session_id}</p>
                  <p className="muted">Updated {formatTimestamp(entry.updated_at)}</p>
                </li>
              ))}
            </ul>
          )}
        </article>
      </div>
    </section>
  );
}
