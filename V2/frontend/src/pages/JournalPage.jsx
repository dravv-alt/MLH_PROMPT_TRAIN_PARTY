import { useAuth } from "@clerk/react";
import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import {
  createJournalEntry,
  deleteJournalEntry,
  listJournalEntries,
  suggestJournalEntries,
  updateJournalEntry,
} from "../services/api";

function parseTurnIds(rawValue) {
  return [...new Set(rawValue.split(/[,\s]+/).map((value) => Number.parseInt(value, 10)).filter((value) => Number.isInteger(value) && value > 0))];
}

function formatTimestamp(isoValue) {
  const parsed = Date.parse(isoValue);
  if (Number.isNaN(parsed)) {
    return "Unknown time";
  }
  return new Date(parsed).toLocaleString();
}

export default function JournalPage() {
  const { getToken } = useAuth();
  const [searchParams] = useSearchParams();

  const [entries, setEntries] = useState([]);
  const [sessionId, setSessionId] = useState(searchParams.get("session_id") || "");
  const [maxSuggestions, setMaxSuggestions] = useState(5);
  const [reasoningLabels, setReasoningLabels] = useState([]);
  const [selectedTurnIdsText, setSelectedTurnIdsText] = useState("");
  const [entryTitle, setEntryTitle] = useState("");
  const [reflectionText, setReflectionText] = useState("");

  const [editingEntryId, setEditingEntryId] = useState(null);
  const [editTitle, setEditTitle] = useState("");
  const [editReflection, setEditReflection] = useState("");

  const [loadingEntries, setLoadingEntries] = useState(false);
  const [saving, setSaving] = useState(false);
  const [notice, setNotice] = useState("");
  const [toast, setToast] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    if (!toast) {
      return undefined;
    }

    const timer = window.setTimeout(() => {
      setToast("");
    }, 2600);

    return () => {
      window.clearTimeout(timer);
    };
  }, [toast]);

  useEffect(() => {
    const querySessionId = searchParams.get("session_id") || "";
    if (querySessionId && !sessionId) {
      setSessionId(querySessionId);
    }
  }, [searchParams, sessionId]);

  useEffect(() => {
    let isActive = true;

    async function loadEntries() {
      setLoadingEntries(true);
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
          setError(apiError.message || "Unable to load journal entries.");
        }
      } finally {
        if (isActive) {
          setLoadingEntries(false);
        }
      }
    }

    loadEntries();
    return () => {
      isActive = false;
    };
  }, [getToken]);

  const refreshEntries = async () => {
    const token = await getToken();
    if (!token) {
      throw new Error("Authentication token not available. Please sign in again.");
    }

    const response = await listJournalEntries(token);
    setEntries(response.entries || []);
  };

  const handleSuggest = async () => {
    if (!sessionId.trim()) {
      setError("Provide a session id to get journal suggestions.");
      return;
    }

    setNotice("");
    setError("");
    setSaving(true);

    try {
      const token = await getToken();
      if (!token) {
        throw new Error("Authentication token not available. Please sign in again.");
      }

      const response = await suggestJournalEntries(sessionId.trim(), Number(maxSuggestions) || 5, token);
      setSelectedTurnIdsText((response.suggested_turn_ids || []).join(", "));
      setReasoningLabels(response.reasoning_labels || []);
      setNotice("Suggestions loaded. You can edit selected turn ids before saving.");
    } catch (apiError) {
      setError(apiError.message || "Unable to suggest journal turns.");
    } finally {
      setSaving(false);
    }
  };

  const handleCreate = async (event) => {
    event.preventDefault();

    if (!sessionId.trim()) {
      setError("Session id is required.");
      return;
    }

    const selectedTurnIds = parseTurnIds(selectedTurnIdsText);
    if (!selectedTurnIds.length) {
      setError("Provide at least one selected turn id.");
      return;
    }

    setNotice("");
    setError("");
    setSaving(true);

    try {
      const token = await getToken();
      if (!token) {
        throw new Error("Authentication token not available. Please sign in again.");
      }

      await createJournalEntry(
        {
          session_id: sessionId.trim(),
          selected_turn_ids: selectedTurnIds,
          entry_title: entryTitle.trim() || null,
          user_reflection_text: reflectionText.trim() || null,
        },
        token
      );

      await refreshEntries();
      setEntryTitle("");
      setReflectionText("");
      setNotice("Journal entry saved.");
      setToast("Journal entry created.");
    } catch (apiError) {
      setError(apiError.message || "Unable to save journal entry.");
    } finally {
      setSaving(false);
    }
  };

  const beginEdit = (entry) => {
    setEditingEntryId(entry.entry_id);
    setEditTitle(entry.entry_title || "");
    setEditReflection(entry.user_reflection_text || "");
    setNotice("");
    setError("");
  };

  const handleSaveEdit = async (entryId) => {
    setNotice("");
    setError("");
    setSaving(true);

    try {
      const token = await getToken();
      if (!token) {
        throw new Error("Authentication token not available. Please sign in again.");
      }

      await updateJournalEntry(
        entryId,
        {
          entry_title: editTitle.trim() || null,
          user_reflection_text: editReflection.trim() || null,
        },
        token
      );

      await refreshEntries();
      setEditingEntryId(null);
      setNotice("Journal entry updated.");
      setToast("Journal entry updated.");
    } catch (apiError) {
      setError(apiError.message || "Unable to update journal entry.");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (entryId) => {
    const confirmed = window.confirm("Delete this journal entry?");
    if (!confirmed) {
      return;
    }

    setNotice("");
    setError("");
    setSaving(true);

    try {
      const token = await getToken();
      if (!token) {
        throw new Error("Authentication token not available. Please sign in again.");
      }

      await deleteJournalEntry(entryId, token);
      await refreshEntries();
      if (editingEntryId === entryId) {
        setEditingEntryId(null);
      }
      setNotice("Journal entry deleted.");
      setToast("Journal entry deleted.");
    } catch (apiError) {
      setError(apiError.message || "Unable to delete journal entry.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <section className="page-panel journal-panel">
      <div className="chat-header">
        <h1>Journal</h1>
        <Link to="/insights" className="ghost-btn inline-link">
          Open Insights
        </Link>
      </div>
      <p className="muted">
        Capture key turns from a reflection session, add your own note, and keep editable snapshots without storing raw conversation logs.
      </p>
      {toast ? (
        <div className="success-toast" role="status" aria-live="polite">
          {toast}
        </div>
      ) : null}

      <article className="card onboarding-card">
        <h3>First time here? Quick path</h3>
        <ol className="onboarding-steps">
          <li>Open <Link to="/chat">Chat</Link> and send at least one message.</li>
          <li>Copy the active session id (or use the journal link shown in chat).</li>
          <li>Use Suggest Turns, then create your journal entry.</li>
        </ol>
      </article>

      <form className="stack-form" onSubmit={handleCreate}>
        <label htmlFor="journal-session-id">Session id</label>
        <input
          id="journal-session-id"
          value={sessionId}
          onChange={(event) => setSessionId(event.target.value)}
          placeholder="Paste a session id from chat"
          required
        />

        <div className="button-row">
          <label htmlFor="max-suggestions">Suggestion count</label>
          <input
            id="max-suggestions"
            type="number"
            min={1}
            max={20}
            value={maxSuggestions}
            onChange={(event) => setMaxSuggestions(event.target.value)}
          />
          <button className="ghost-btn" type="button" onClick={handleSuggest} disabled={saving}>
            {saving ? "Working..." : "Suggest Turns"}
          </button>
        </div>

        {reasoningLabels.length ? (
          <p className="muted">Reasoning labels: {reasoningLabels.join(", ")}</p>
        ) : (
          <p className="muted">No reasoning labels yet. Use Suggest Turns after setting session id.</p>
        )}

        <label htmlFor="selected-turn-ids">Selected turn ids (comma or space separated)</label>
        <textarea
          id="selected-turn-ids"
          rows={2}
          value={selectedTurnIdsText}
          onChange={(event) => setSelectedTurnIdsText(event.target.value)}
          placeholder="Example: 14, 15, 18"
        />

        <label htmlFor="entry-title">Entry title (optional)</label>
        <input
          id="entry-title"
          value={entryTitle}
          onChange={(event) => setEntryTitle(event.target.value)}
          maxLength={200}
          placeholder="What this reflection means to you"
        />

        <label htmlFor="entry-reflection">Your reflection note (optional)</label>
        <textarea
          id="entry-reflection"
          rows={4}
          value={reflectionText}
          onChange={(event) => setReflectionText(event.target.value)}
          maxLength={5000}
          placeholder="Add your own context, what shifted, or what you want to revisit."
        />

        {error ? <p className="error-text">{error}</p> : null}
        {notice ? <p className="muted">{notice}</p> : null}

        <button className="primary-btn" type="submit" disabled={saving}>
          {saving ? "Saving..." : "Create Journal Entry"}
        </button>
      </form>

      <div className="entries-header">
        <h2>Saved entries</h2>
        {loadingEntries ? <p className="muted">Loading entries...</p> : null}
      </div>

      <div className="stack-list">
        {!loadingEntries && entries.length === 0 ? (
          <article className="card">
            <p className="muted">No entries yet. Start from chat, then create your first journal snapshot here.</p>
            <p className="muted">Tip: if you arrived from chat using the handoff link, your session id is already pre-filled.</p>
          </article>
        ) : null}

        {entries.map((entry) => (
          <article key={entry.entry_id} className="card">
            <p className="eyebrow">Session {entry.session_id}</p>
            <h3>{entry.entry_title || "Untitled reflection"}</h3>
            <p className="muted">
              Turns: {entry.selected_turn_ids.join(", ")} | Labels: {entry.reasoning_labels.join(", ") || "none"}
            </p>
            <p>{entry.summary_snapshot}</p>
            {entry.user_reflection_text ? <p>{entry.user_reflection_text}</p> : null}
            <p className="muted">Updated {formatTimestamp(entry.updated_at)}</p>

            {editingEntryId === entry.entry_id ? (
              <div className="stack-form">
                <input value={editTitle} onChange={(event) => setEditTitle(event.target.value)} maxLength={200} />
                <textarea
                  rows={3}
                  value={editReflection}
                  onChange={(event) => setEditReflection(event.target.value)}
                  maxLength={5000}
                />
                <div className="button-row">
                  <button className="primary-btn" type="button" onClick={() => handleSaveEdit(entry.entry_id)} disabled={saving}>
                    Save
                  </button>
                  <button className="ghost-btn" type="button" onClick={() => setEditingEntryId(null)} disabled={saving}>
                    Cancel
                  </button>
                </div>
              </div>
            ) : (
              <div className="button-row">
                <button className="ghost-btn" type="button" onClick={() => beginEdit(entry)} disabled={saving}>
                  Edit
                </button>
                <button className="text-btn" type="button" onClick={() => handleDelete(entry.entry_id)} disabled={saving}>
                  Delete
                </button>
              </div>
            )}
          </article>
        ))}
      </div>
    </section>
  );
}
