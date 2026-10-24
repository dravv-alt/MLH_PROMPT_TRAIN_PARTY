import {useEffect,useState} from 'react';
import {Link} from 'react-router-dom';
import {searchMemory,getClassification,previewClassification,getNeuralPreferences,setNeuralPreferences} from '../services/api';

export default function NeuralTools({analysis,getToken,previewText,compact=false}) {
  const [share,setShare]=useState(false),[prefsReady,setPrefsReady]=useState(false);
  const [error,setError]=useState(''),[query,setQuery]=useState(''),[search,setSearch]=useState(null),[busy,setBusy]=useState(false);
  const [open,setOpen]=useState(false),[classification,setClassification]=useState(null);
  const turn=analysis?.classification?.turn_id;
  useEffect(()=>{if(!getToken)return;let active=true;getToken().then(getNeuralPreferences).then(p=>{if(active){setShare(p.share_history_with_provider);setPrefsReady(true);}}).catch(e=>{if(active)setError(e.message);});return()=>{active=false;};},[getToken]);
  useEffect(()=>{setClassification(analysis?.classification||null);setSearch(null);},[analysis]);
  useEffect(()=>{
    let active=true,timer;
    async function poll(){try{const value=await getClassification(turn,await getToken());if(!active)return;setClassification(value);if(['pending','running'].includes(value.status))timer=setTimeout(poll,2000);}catch(e){if(active)setError(e.message);}}
    if((open||compact)&&turn&&getToken&&document.visibilityState!=='hidden')poll();
    return()=>{active=false;clearTimeout(timer);};
  },[turn,open,compact,getToken]);
  async function preference(e){const value=e.target.checked;setPrefsReady(false);try{const result=await setNeuralPreferences(value,await getToken());setShare(result.share_history_with_provider);}catch(err){setError(err.message);}finally{setPrefsReady(true);}}
  async function find(e){e.preventDefault();setBusy(true);setError('');try{setSearch(await searchMemory(query,await getToken()));}catch(err){setError(err.message);}finally{setBusy(false);}}
  async function classify(){setClassification({status:'pending'});try{setClassification(await previewClassification(previewText||analysis.redacted_text,await getToken()));}catch(err){setError(err.message);setClassification({status:'unavailable'});}}
  const retrieval=search||analysis?.semantic_retrieval;
  const canonical=classification?.redacted_text||analysis?.redacted_text||'';
  return <section className={compact ? "compact-neural-tools" : "nlp-panel"}><h2>Local neural memory</h2>
    {getToken&&<label><input type="checkbox" checked={share} disabled={!prefsReady} onChange={preference}/> Allow historical excerpts in provider responses</label>}
    <p>Off by default. When enabled, up to three redacted excerpts (300 characters each) may leave this application. Local search works without sharing.</p>
    {getToken?<form onSubmit={find}><label>Search conversation memory<input aria-label="Search conversation memory" value={query} onChange={e=>setQuery(e.target.value)} maxLength={2000} required/></label><button disabled={busy}>{busy?'Searching…':'Search local memory'}</button></form>:<p>Offline synthetic walkthrough: recorded local model outputs; no requests or provider sharing.</p>}
    {retrieval&&<><p>{retrieval.status} · {retrieval.method} · index {retrieval.index_revision}. Indexed {retrieval.coverage?.indexed_scenes} / {retrieval.coverage?.eligible_scenes} eligible scenes. {retrieval.reason}</p><p>Exploratory matches, not verified relevance.</p>{retrieval.results?.map(s=><article key={`${s.source_turn_id}:${s.scene_id}`}><h3>{s.scene_id}</h3><p>Query match: <mark>{s.query_excerpt||query}</mark></p><blockquote><mark>{s.excerpt}</mark></blockquote><p>Lexical {s.lexical_score??'—'} · semantic {s.semantic_score??'—'} · RRF {s.fusion_score}</p>{s.source_session_id&&(getToken?<Link to={`/analysis?session_id=${encodeURIComponent(s.source_session_id)}&turn_id=${s.source_turn_id}`}>Source turn {s.source_turn_id}</Link>:<p>Synthetic source turn {s.source_turn_id}</p>)}</article>)}</>}
    <details open={compact || open} onToggle={e=>setOpen(e.currentTarget.open)}><summary>Experimental zero-shot suggestions</summary><p>Not validated on Sanctuary conversations. Adjusted scores are not calibrated confidence.</p>
      {!turn&&analysis&&getToken&&<button onClick={classify}>Classify preview locally</button>}
      <p role="status">Classification: {classification?.status||'not requested'} {classification?.reason}</p>
      {classification?.status==='ready'&&<><p>{classification.premise_count} premises; maximum aggregation can favor longer turns.</p>{classification.suggestions?.length?classification.suggestions.map(l=><article key={l.label}><strong>{l.group}: {l.label}</strong><p>Adjusted {l.adjusted_score}; entailment {l.entailment}</p><mark>{l.spans.map(([a,b])=>canonical.slice(a,b)).join(' … ')}</mark></article>):<p>No suggestions.</p>}<details><summary>All label scores</summary><table><thead><tr><th>Label</th><th>Entailment</th><th>Neutral</th><th>Contradiction</th><th>Adjusted</th></tr></thead><tbody>{classification.labels.map(l=><tr key={l.label}><td>{l.label}</td><td>{l.entailment}</td><td>{l.neutral}</td><td>{l.contradiction}</td><td>{l.adjusted_score}</td></tr>)}</tbody></table></details></>}
    </details>{error&&<p role="alert">{error}</p>}
  </section>;
}
