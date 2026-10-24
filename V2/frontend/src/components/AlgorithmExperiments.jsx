import {useEffect, useRef, useState} from 'react';
import {runAlgorithmExperiments} from '../services/api';

export default function AlgorithmExperiments({text, sessionId, getToken}) {
  const [result, setResult] = useState(null), [busy, setBusy] = useState(false), [error, setError] = useState('');
  const revision = useRef(0);
  useEffect(() => { revision.current += 1; setResult(null); setError(''); setBusy(false);
    return () => { revision.current += 1; };
  }, [text, sessionId]);
  async function run() {
    const current = ++revision.current;
    setBusy(true); setError('');
    try {
      const response = await runAlgorithmExperiments(text, sessionId || null, await getToken());
      if(current === revision.current) setResult(response);
    } catch(e) { if(current === revision.current) setError(e.message); }
    finally { if(current === revision.current) setBusy(false); }
  }
  return <section className="nlp-panel" aria-label="Algorithm experiments">
    <h2>Compare experimental algorithms</h2>
    <p>Run Porter stemming, restricted suffix FST, regex/spaCy/WordPiece tokenization, n-grams, Laplace and approximate Good–Turing smoothing, TF-IDF, LSA/SVD, document PPMI, and token-superposition VSA locally.</p>
    <p>Read-only diagnostics. No model downloads or provider calls. These comparisons do not change your response or memory. Select a session with earlier turns for retrieval and held-out perplexity.</p>
    <button disabled={busy || !text?.trim()} onClick={run}>{busy ? 'Running local comparisons…' : 'Run algorithm comparisons'}</button>
    {error && <p role="alert">{error}</p>}
    {result && <><p>{result.document_count} documents · {result.boundary}</p>
      {Object.entries(result.tokenization || {}).map(([name, value]) => <details key={name}><summary>{name.replaceAll('_', ' ')} — {value.status}</summary><pre>{JSON.stringify(value, null, 2)}</pre></details>)}
      <details><summary>N-grams and smoothing — {result.language_models?.status}</summary><pre>{JSON.stringify(result.language_models, null, 2)}</pre></details>
      <details><summary>Retrieval representation comparisons</summary><pre>{JSON.stringify(result.retrieval, null, 2)}</pre></details>
    </>}
  </section>;
}
