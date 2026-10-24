import { useAuth } from '@clerk/react';
import { useState, useEffect, useRef } from 'react';
import {useLocation} from 'react-router-dom';
import NLPPanel from '../components/NLPPanel';
import { analyzeText, getAnalysisHistory, getWorldMemory, eraseWorldMemory, getWorldGraph, reviewMemoryItem, listSessions } from '../services/api';
import WorldMemory from '../components/WorldMemory';
import AlgorithmExperiments from '../components/AlgorithmExperiments';

export default function AnalysisPage() {
  const { getToken } = useAuth();
  return <AnalysisWorkspace getToken={getToken}/>;
}

export function AnalysisWorkspace({getToken}) {
  const {search} = useLocation();
  const request = useRef(0);
  const [text,setText]=useState('');
  const [session,setSession]=useState(new URLSearchParams(location.search).get('session_id') || '');
  const [sessions,setSessions]=useState([]), [profile,setProfile]=useState('balanced');
  const [analysis,setAnalysis]=useState(null), [records,setRecords]=useState([]), [error,setError]=useState(''), [busy,setBusy]=useState(false);
  const [memory,setMemory]=useState(null);
  const [graph,setGraph]=useState(null);
  useEffect(()=>{let active=true;getToken().then(listSessions).then(result=>{if(active)setSessions(result.sessions || []);}).catch(e=>{if(active)setError(e.message);});return()=>{active=false;};},[getToken]);
  useEffect(()=>{setSession(new URLSearchParams(search).get('session_id') || '');},[search]);
  useEffect(()=>{
    const source=new URLSearchParams(search).get('turn_id');let active=true;
    request.current+=1;setBusy(false);setAnalysis(null);setRecords([]);setError('');
    if(session)getToken().then(token=>getAnalysisHistory(session,token)).then(history=>{
      if(!active)return;setRecords(history.records);const record=source?history.records.find(r=>String(r.turn_id)===source):history.records.at(-1);
      if(record){setAnalysis(record.analysis);setText(record.analysis.redacted_text || '');}else if(source)setError('Source turn is no longer available.');
    }).catch(e=>{if(active)setError(e.message);});
    return()=>{active=false;request.current+=1;};
  },[session,getToken,search]);
  async function loadMemory(){try{const token=await getToken();const [m,g]=await Promise.all([getWorldMemory(token),getWorldGraph(token)]);setMemory(m);setGraph(g);}catch(e){setError(e.message);}}
  async function review(id,status){try{await reviewMemoryItem(id,status,memory.revision,await getToken());await loadMemory();}catch(e){setError(e.message);}}
  async function eraseMemory(){if(!window.confirm('Erase your current world memory? Historical chat records remain.'))return;try{await eraseWorldMemory(await getToken());setMemory(null);setAnalysis(null);}catch(e){setError(e.message);}}
  async function submit(e){e.preventDefault();const id=++request.current;setBusy(true);setError('');try {const token=await getToken();const result=await analyzeText(text,session||null,token,profile);if(id===request.current)setAnalysis(result.nlp_analysis);}catch(err){if(id===request.current)setError(err.message);}finally{if(id===request.current)setBusy(false);}}
  return <section className="page-panel"><h1>How this was read</h1>
    <p>Run the real backend pipeline without saving a turn. Choose a conversation to supply prior context; a preview never commits its proposed state.</p>
    <form onSubmit={submit}>
      <label>Conversation context<select aria-label="Analysis conversation" value={session} onChange={e=>setSession(e.target.value)}><option value="">No session context</option>{sessions.map(s=><option key={s.session_id} value={s.session_id}>{new Date(s.updated_at).toLocaleString()} · {s.turn_count} turns</option>)}{session&&!sessions.some(s=>s.session_id===session)&&<option value={session}>{session}</option>}</select></label>
      <label>Mathematical profile<select aria-label="Mathematical profile" value={profile} onChange={e=>setProfile(e.target.value)}>{['low_resource','balanced','high_fidelity','responsive','stable'].map(p=><option key={p} value={p}>{p.replaceAll('_',' ')}</option>)}</select></label>
      <p>Each profile runs linear KF, EKF, UKF, EnKF and particle filtering. Profiles change engineering parameters, not validated human-state measurements.</p>
      <label>Reflection<textarea maxLength={2000} rows={4} value={text} onChange={e=>setText(e.target.value)} required/></label>
      <button className="primary-btn" disabled={busy}>{busy?'Analyzing…':'Analyze preview'}</button>
    </form>
    <AlgorithmExperiments text={text} sessionId={session} getToken={getToken}/>
    <div className="topic-cards"><button onClick={loadMemory}>Load my world memory</button><button onClick={eraseMemory}>Erase current world memory</button></div>
    <WorldMemory memory={memory} graph={graph} onReview={review}/>{error&&<p role="alert">{error}</p>}
    <NLPPanel analysis={analysis} records={records} getToken={getToken} previewText={text}/>
  </section>;
}
