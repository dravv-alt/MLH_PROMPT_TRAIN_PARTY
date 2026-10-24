const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || '/api').replace(/\/$/, '');

function authHeaders(token) {
  return token
    ? {
        Authorization: `Bearer ${token}`,
      }
    : {};
}

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
  });

  if (!response.ok) {
    let detail = { message: "Something went wrong." };
    try {
      const body = await response.json();
      detail = body.error || body.detail || detail;
    } catch {
      // Ignore non-JSON error bodies.
    }
    const error = new Error(detail.message || "Request failed.");
    error.code = detail.code || "request_failed";
    error.status = response.status;
    throw error;
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}

export function sendChatMessage(message, sessionId, casualMode, token, requestId = crypto.randomUUID(), generation = {}) {
  return request("/chat", {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify({ message, session_id: sessionId, casual_mode: casualMode, request_id: requestId, ...generation }),
  });
}

export function listSessions(token) { return request('/sessions', {headers: authHeaders(token)}); }
export function deleteSession(id,token) { return request(`/sessions/${encodeURIComponent(id)}`, {method:'DELETE',headers:authHeaders(token)}); }
export function getGenerationStatus(token) { return request('/nlp/generation/status', {headers:authHeaders(token)}); }
export function queueBackfill(token) { return request('/nlp/neural/backfill', {method:'POST',headers:authHeaders(token)}); }
export function listCalendarEntries(token) { return request('/journal/calendar', {headers:authHeaders(token)}); }
export function saveCalendarEntry(date,entry,token) { return request(`/journal/calendar/${encodeURIComponent(date)}`, {method:'PUT',headers:authHeaders(token),body:JSON.stringify(entry)}); }
export function deleteCalendarEntry(date,token) { return request(`/journal/calendar/${encodeURIComponent(date)}`, {method:'DELETE',headers:authHeaders(token)}); }

export function analyzeText(text, sessionId, token, mathematicalProfile = 'balanced') {
  return request('/nlp/analyze', { method: 'POST', headers: authHeaders(token), body: JSON.stringify({text, session_id: sessionId, mathematical_profile: mathematicalProfile}) });
}

export function runAlgorithmExperiments(text, sessionId, token) {
  return request('/nlp/experiments', {method:'POST',headers:authHeaders(token),body:JSON.stringify({text, session_id:sessionId})});
}

export function getAnalysisHistory(sessionId, token) {
  return request(`/sessions/${encodeURIComponent(sessionId)}/analysis`, {headers: authHeaders(token)});
}

export function getWorldMemory(token) { return request('/nlp/memory', {headers:authHeaders(token)}); }
export function searchMemory(query,token,limit=3) {return request('/nlp/memory/search',{method:'POST',headers:authHeaders(token),body:JSON.stringify({query,limit})});}
export function getClassification(id,token) {return request(`/nlp/turns/${id}/classification`,{headers:authHeaders(token)});}
export function previewClassification(text,token) {return request('/nlp/classification/preview',{method:'POST',headers:authHeaders(token),body:JSON.stringify({text})});}
export function getNeuralPreferences(token) {return request('/nlp/preferences',{headers:authHeaders(token)});}
export function setNeuralPreferences(share,token) {return request('/nlp/preferences',{method:'PATCH',headers:authHeaders(token),body:JSON.stringify({share_history_with_provider:share})});}
export function setLocalProcessingPreference(enabled,token) {return request('/nlp/preferences',{method:'PATCH',headers:authHeaders(token),body:JSON.stringify({process_local_unredacted:enabled})});}
export function setLocalMemoryPreference(enabled,token) {return request('/nlp/preferences',{method:'PATCH',headers:authHeaders(token),body:JSON.stringify({store_local_unredacted_memory:enabled})});}
export function getNeuralStatus(token) { return request('/nlp/neural/status', {headers:authHeaders(token)}); }
export function eraseWorldMemory(token) { return request('/nlp/memory', {method:'DELETE',headers:authHeaders(token)}); }
export function getWorldGraph(token) { return request('/nlp/memory/graph', {headers:authHeaders(token)}); }
export function reviewMemoryItem(id,status,revision,token) { return request(`/nlp/memory/unresolved/${encodeURIComponent(id)}`, {method:'PATCH',headers:authHeaders(token),body:JSON.stringify({status,expected_revision:revision})}); }

export function getSessionTurns(sessionId, token) {
  return request(`/sessions/${encodeURIComponent(sessionId)}/turns`, {
    headers: authHeaders(token),
  });
}

export function suggestJournalEntries(sessionId, maxSuggestions, token) {
  return request("/journal/suggest", {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify({
      session_id: sessionId,
      max_suggestions: maxSuggestions,
    }),
  });
}

export function createJournalEntry(payload, token) {
  return request("/journal/create", {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify(payload),
  });
}

export function listJournalEntries(token) {
  return request("/journal", {
    headers: authHeaders(token),
  });
}

export function updateJournalEntry(entryId, payload, token) {
  return request(`/journal/${entryId}`, {
    method: "PATCH",
    headers: authHeaders(token),
    body: JSON.stringify(payload),
  });
}

export function deleteJournalEntry(entryId, token) {
  return request(`/journal/${entryId}`, {
    method: "DELETE",
    headers: authHeaders(token),
  });
}

export function getEmergencyResources() {
  return request("/resources/emergency");
}
