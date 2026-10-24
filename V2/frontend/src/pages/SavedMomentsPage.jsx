import {useAuth} from '@clerk/react';
import {useEffect,useState} from 'react';
import {Link,useSearchParams} from 'react-router-dom';
import {listJournalEntries,createJournalEntry,updateJournalEntry,deleteJournalEntry,suggestJournalEntries,listSessions,getSessionTurns} from '../services/api';

export default function SavedMomentsPage(){const {getToken}=useAuth();return <SavedMomentsWorkspace getToken={getToken}/>;}
export function SavedMomentsWorkspace({getToken}){
  const [params]=useSearchParams();
  const [session,setSession]=useState(params.get('session_id')||''),[sessions,setSessions]=useState([]),[turns,setTurns]=useState([]),[selected,setSelected]=useState([]);
  const [entries,setEntries]=useState([]),[title,setTitle]=useState(''),[note,setNote]=useState(''),[editing,setEditing]=useState(null);
  const [busy,setBusy]=useState(false),[error,setError]=useState(''),[notice,setNotice]=useState('');
  async function refresh(){setEntries((await listJournalEntries(await getToken())).entries || []);}
  useEffect(()=>{let active=true;setBusy(true);getToken().then(token=>Promise.all([listJournalEntries(token),listSessions(token)])).then(([e,s])=>{if(active){setEntries(e.entries);setSessions(s.sessions);}}).catch(e=>{if(active)setError(e.message);}).finally(()=>{if(active)setBusy(false);});return()=>{active=false;};},[getToken]);
  useEffect(()=>{let active=true;setSelected([]);setTurns([]);if(session)getToken().then(token=>getSessionTurns(session,token)).then(r=>{if(active)setTurns(r.turns);}).catch(e=>{if(active)setError(e.message);});return()=>{active=false;};},[session,getToken]);
  async function suggest(){setBusy(true);setError('');try{const r=await suggestJournalEntries(session,5,await getToken());setSelected(r.suggested_turn_ids);setNotice('Suggested turns selected. Review them before saving.');}catch(e){setError(e.message);}finally{setBusy(false);}}
  async function save(e){e.preventDefault();setBusy(true);setError('');try{const token=await getToken();const fields={entry_title:title.trim()||null,user_reflection_text:note.trim()||null};if(editing)await updateJournalEntry(editing,fields,token);else await createJournalEntry({...fields,session_id:session,selected_turn_ids:selected},token);await refresh();setEditing(null);setTitle('');setNote('');setSelected([]);setNotice('Moment saved to your journal.');}catch(e){setError(e.message);}finally{setBusy(false);}}
  async function remove(id){if(!window.confirm('Delete this saved moment?'))return;setBusy(true);try{await deleteJournalEntry(id,await getToken());await refresh();setNotice('Moment deleted.');}catch(e){setError(e.message);}finally{setBusy(false);}}
  return <section className="page-panel"><header className="workspace-header"><div><p className="eyebrow">Saved conversation snapshots</p><h1>Moments</h1><p>Choose the turns you want to keep and add your own note.</p></div><Link className="ghost-btn" to="/journal">Open calendar journal</Link></header>
    {error&&<p role="alert" className="error-text">{error}</p>}{notice&&<p role="status">{notice}</p>}
    <form className="stack-form" onSubmit={save}>
      {!editing&&<><label>Conversation<select value={session} onChange={e=>setSession(e.target.value)} required disabled={busy}><option value="">Choose a conversation</option>{sessions.map(s=><option key={s.session_id} value={s.session_id}>{new Date(s.updated_at).toLocaleString()} · {s.turn_count} turns</option>)}</select></label>
      <button className="ghost-btn" type="button" disabled={busy||!session} onClick={suggest}>Suggest turns</button>
      <fieldset><legend>Turns to save</legend>{turns.length?turns.map(t=><label className="journal-turn" key={t.turn_id}><input type="checkbox" checked={selected.includes(t.turn_id)} onChange={e=>setSelected(prev=>e.target.checked?[...prev,t.turn_id]:prev.filter(id=>id!==t.turn_id))}/>Turn {t.turn_index}: {t.identity_stripped_input}</label>):<p>Choose a saved conversation to see its turns.</p>}</fieldset></>}
      <label>Title<input maxLength={200} value={title} onChange={e=>setTitle(e.target.value)}/></label><label>Your note<textarea maxLength={5000} rows={3} value={note} onChange={e=>setNote(e.target.value)}/></label>
      <div className="button-row"><button className="primary-btn" disabled={busy||(!editing&&(!session||!selected.length))}>{busy?'Saving…':editing?'Update moment':'Save moment'}</button>{editing&&<button type="button" onClick={()=>{setEditing(null);setTitle('');setNote('');}}>Cancel edit</button>}</div>
    </form>
    <h2>Saved moments</h2>{busy&&<p role="status">Working…</p>}{!busy&&!entries.length&&<p>No saved moments yet.</p>}
    <div className="stack-list">{entries.map(e=><article className="evidence-card" key={e.entry_id}><h3>{e.entry_title||'Untitled moment'}</h3><p>{e.summary_snapshot}</p>{e.user_reflection_text&&<p>{e.user_reflection_text}</p>}<small>{new Date(e.updated_at).toLocaleString()} · turns {e.selected_turn_ids.join(', ')}</small><div className="button-row"><Link to={`/talk?session_id=${e.session_id}`}>Source conversation</Link><button disabled={busy} onClick={()=>{setEditing(e.entry_id);setTitle(e.entry_title||'');setNote(e.user_reflection_text||'');}}>Edit</button><button disabled={busy} onClick={()=>remove(e.entry_id)}>Delete</button></div></article>)}</div>
  </section>;
}
