import { useAuth } from '@clerk/react';
import { useEffect, useRef, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { sendChatMessage, getAnalysisHistory, getSessionTurns, listSessions, deleteSession, getGenerationStatus } from '../services/api';
import NLPPanel from '../components/NLPPanel';
import TurnInsightDrawer from '../components/TurnInsightDrawer';
import PebblePet3D from '../components/PebblePet3D';

const historyText = text => String(text || '[Text unavailable]').replace(/\[entity_e\d+\]/g,'someone');

export default function ChatPage() {
  const {getToken} = useAuth();
  return <ChatWorkspace getToken={getToken}/>;
}

export function ChatWorkspace({getToken}) {
  const [params,setParams] = useSearchParams();
  const sessionId = params.get('session_id') || null;
  const loadedSession = useRef(null), pending = useRef(null), end = useRef(null);
  const [sessions,setSessions] = useState([]), [messages,setMessages] = useState([]);
  const [draft,setDraft] = useState(''), [records,setRecords] = useState([]), [analysis,setAnalysis] = useState(null);
  const [loading,setLoading] = useState(false), [hydrating,setHydrating] = useState(false), [error,setError] = useState('');
  const [mode,setMode] = useState(''), [casual,setCasual] = useState(false), [drawer,setDrawer] = useState(null);
  const [provider,setProvider] = useState('local'), [consent,setConsent] = useState(false), [generation,setGeneration] = useState(null);
  const [pet,setPet] = useState(true);
  const busy = loading || hydrating;
  const source = id => `/how-this-was-read?session_id=${encodeURIComponent(sessionId)}&turn_id=${id}`;

  async function refreshSessions() { setSessions((await listSessions(await getToken())).sessions); }
  useEffect(()=>{let active=true; getToken().then(token=>Promise.all([listSessions(token),getGenerationStatus(token)])).then(([list,status])=>{
    if(active){setSessions(list.sessions);setGeneration(status);}
  }).catch(e=>{if(active)setError(e.message);}); return()=>{active=false;};},[getToken]);

  useEffect(()=>{
    if (loadedSession.current === sessionId) return;
    let active=true;
    pending.current=null; setError('');setDrawer(null);
    if(!sessionId){setMessages([]);setRecords([]);setAnalysis(null);setMode('');loadedSession.current=null;setHydrating(false);return;}
    setHydrating(true);
    getToken().then(token=>Promise.all([getSessionTurns(sessionId,token),getAnalysisHistory(sessionId,token)])).then(([history,historyAnalysis])=>{
      if(!active)return;
      setRecords(historyAnalysis.records || []);setAnalysis(historyAnalysis.records?.at(-1)?.analysis || null);
      setMessages(history.turns.flatMap(t=>[{role:'user',text:historyText(t.identity_stripped_input),id:t.turn_id}, {role:'assistant',text:historyText(t.response_text),id:t.turn_id,mode:t.safety_mode}]));
      setMode(history.turns.at(-1)?.safety_mode || '');loadedSession.current=sessionId;
    }).catch(e=>{if(active){setMessages([]);setRecords([]);setAnalysis(null);setError(e.message);}}).finally(()=>{if(active)setHydrating(false);});
    return()=>{active=false;};
  },[sessionId,getToken]);
  useEffect(()=>{end.current?.scrollIntoView({behavior:'smooth',block:'nearest'});},[messages.length,loading]);

  async function handleSubmit(event) {
    event.preventDefault();
    if(!draft.trim() || busy)return;
    const text=draft.trim(), signature=JSON.stringify([text,sessionId,casual,provider,consent]);
    if(!pending.current || pending.current.signature!==signature) pending.current={signature,id:crypto.randomUUID()};
    setLoading(true);setError('');
    try{
      const token=await getToken();if(!token)throw new Error('Sign in again to continue.');
      const response=await sendChatMessage(text,sessionId,casual,token,pending.current.id,{generation_provider:provider,hosted_consent:provider==='hosted'&&consent});
      loadedSession.current=response.session_id;
      setParams({session_id:response.session_id},{replace:true});
      setAnalysis(response.nlp_analysis);setMode(response.safety_mode);setDraft('');pending.current=null;
      setMessages(prev=>[...prev,{role:'user',text,id:response.turn_id},{role:'assistant',text:response.display_response_text || response.response_text,id:response.turn_id,mode:response.safety_mode}]);
      setRecords(prev=>[...prev,{turn_id:response.turn_id,analysis:response.nlp_analysis}]);
      try{await refreshSessions();}catch{setError('Your turn was saved. Conversation list could not refresh.');}
    }catch(e){
      setError(e.message || 'Unable to send. Your draft is still here.');
      if(['session_changed','preferences_changed','request_reused'].includes(e.code)){
        pending.current=null;
        if(sessionId){try{const token=await getToken();const [h,a]=await Promise.all([getSessionTurns(sessionId,token),getAnalysisHistory(sessionId,token)]);setMessages(h.turns.flatMap(t=>[{role:'user',text:t.identity_stripped_input,id:t.turn_id},{role:'assistant',text:t.response_text,id:t.turn_id}]));setRecords(a.records);setAnalysis(a.records.at(-1)?.analysis);}catch{setError('Conversation changed; refresh this page before retrying. Your draft is still here.');}}
      }
    }finally{setLoading(false);}
  }

  async function removeSession(){
    if(!sessionId || !window.confirm('Delete this conversation and its source memory? Saved journal snapshots remain.'))return;
    setLoading(true);setError('');
    try{await deleteSession(sessionId,await getToken());setParams({});await refreshSessions();}
    catch(e){setError(e.message);}finally{setLoading(false);}
  }
  return <section className="page-panel chat-panel live-talk">
    <header className="workspace-header"><div><p className="eyebrow">Your conversation</p><h1>Talk</h1><p className="muted">Share what is on your mind. Conversations are saved to the Sanctuary backend.</p></div><button className="ghost-btn" disabled={busy} onClick={()=>setParams({})}>New conversation</button></header>
    <div className="conversation-toolbar">
      <label>Conversation<select aria-label="Conversation" value={sessionId || ''} disabled={busy} onChange={e=>setParams(e.target.value?{session_id:e.target.value}:{})}><option value="">New conversation</option>{sessions.map(s=><option key={s.session_id} value={s.session_id}>{new Date(s.updated_at).toLocaleString()} · {s.turn_count} turns</option>)}</select></label>
      {sessionId&&<><Link className="ghost-btn inline-link" to={`/moments?session_id=${sessionId}`}>Save a moment</Link><button className="text-btn" disabled={busy} onClick={removeSession}>Delete conversation</button></>}
    </div>
    <div className="timeline" aria-live="polite" aria-busy={busy}>
      {!messages.length&&!busy&&<p className="empty-state">Start with a thought, an event or something you want to put into words.</p>}
      {hydrating&&<p role="status">Opening conversation…</p>}
      {messages.map((message,i)=><article key={`${message.id}-${message.role}-${i}`} className={`bubble ${message.role}`}><p>{message.text}</p>{message.id&&<div className="message-actions"><button className="text-btn" onClick={()=>setDrawer(records.find(r=>r.turn_id===message.id)?.analysis || analysis)}>Turn insights</button><Link to={source(message.id)}>Full analysis</Link></div>}</article>)}
      {loading&&<p role="status" className="processing-indicator"><span className="processing-dot"/>Processing your message…</p>}
      <div ref={end}/>
    </div>
    {pet&&<div className="live-companion"><PebblePet3D lifecycleState={loading?'thinking':draft?'attentive':'idle'} isTyping={Boolean(draft)} statusText={loading?'Reflecting…':'Here with you'} className="w-full h-full"/></div>}
    <form className="chat-form" onSubmit={handleSubmit}>
      <label htmlFor="chat-draft">Your message</label><textarea id="chat-draft" rows={3} maxLength={2000} value={draft} onChange={e=>setDraft(e.target.value)} onKeyDown={e=>{if(e.key==='Enter'&&!e.shiftKey&&!e.nativeEvent.isComposing){e.preventDefault();handleSubmit(e);}}} disabled={busy} placeholder="Write here…" required/>
      <div className="conversation-toolbar"><label>Generation<select value={provider} onChange={e=>{setProvider(e.target.value);setConsent(false);}} disabled={busy}><option value="local">Local model</option><option value="hosted" disabled={!generation?.hosted?.configured}>Hosted model {generation?.hosted?.configured?'':'(not configured)'}</option></select></label><label className="toggle-row"><input type="checkbox" checked={casual} onChange={e=>setCasual(e.target.checked)} disabled={busy}/>Casual tone</label><label className="toggle-row"><input type="checkbox" checked={pet} onChange={e=>setPet(e.target.checked)}/>Companion</label><span className="muted">{draft.length}/2000</span></div>
      {provider==='hosted'&&<label className="settings-card"><input type="checkbox" checked={consent} onChange={e=>setConsent(e.target.checked)} disabled={busy}/> Allow this redacted message to be sent to {generation?.hosted?.provider}. Historical excerpts are sent only if enabled in <Link to="/privacy">Privacy</Link>. Rejected hosted responses return an error after retries.</label>}
      {error&&<p className="error-text" role="alert">{error}</p>}
      <button className="primary-btn" disabled={busy||!draft.trim()||(provider==='hosted'&&!consent)}>{loading?'Reflecting…':'Send'}</button>
    </form>
    {mode&&<p role="status" className="muted">Response: {mode==='classical_local_fallback'?'Local fallback — the model draft did not pass validation':mode==='hosted_polish'?'Hosted model, locally validated':mode==='reflective_local_transformer'?'Local Transformer':'Local response'}</p>}
    {drawer&&<TurnInsightDrawer analysis={drawer} getToken={getToken} onClose={()=>setDrawer(null)}/>}
    <details className="technical-details"><summary>Explore backend analysis</summary><NLPPanel analysis={analysis} records={records} status="committed" getToken={getToken}/></details>
  </section>;
}
