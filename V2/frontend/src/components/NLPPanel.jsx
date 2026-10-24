import { useState, useEffect } from 'react';
import NeuralTools from './NeuralTools';
import BackendCoreDetails from './BackendCoreDetails';
import AlgorithmInventory from './AlgorithmInventory';
import {analysisRecord} from '../services/analysisRecord';

const names = {entity_continuity:'Entity continuity', connective_density:'Connective density', hedge_density:'Hedge density', topic_novelty:'Topic novelty'};
const value = x => typeof x !== 'number' ? 'Unavailable' : x.toFixed(3);

export default function NLPPanel({ analysis, records = [], status = 'preview', getToken, previewText }) {
  const [selected, setSelected] = useState(null);
  const [topic, setTopic] = useState(null);
  const [turnSelection,setTurnSelection] = useState('latest');
  useEffect(()=>{setSelected(null);setTurnSelection('latest');},[analysis]);
  const source = turnSelection === 'latest' ? analysis : records[Number(turnSelection)]?.analysis || analysis;
  const a = analysisRecord(source);
  if (!a) return null;
  const clauseIndex = Object.fromEntries(a.clauses.map((c,i) => [c.id, i]));
  const edge = a.relations.find(r => r.id === selected);
  const highlight = edge ? [edge.cue_span, ...a.clauses.filter(c => c.id === edge.arg1 || c.id === edge.arg2).flatMap(c => c.spans)] : a.mentions.map(m => m.span);
  const boundaries = [...new Set([0, a.redacted_text.length, ...highlight.flat()])].sort((x,y)=>x-y);
  const history = [...records.map(r=>analysisRecord(r.analysis)).filter(Boolean), ...(status === 'preview' ? [a] : records.length ? [] : [a])];
  return <section className="nlp-panel" aria-label="NLP analysis">
    <header><h2>Text analysis</h2><span>{status} · {a.schema_version}</span></header>
    <AlgorithmInventory analysis={source}/>
    <p className="processing-boundary"><strong>Local processing:</strong> {a.local_processing_mode === 'unredacted_transient' ? 'original text used transiently; persisted and provider-facing data remains redacted' : 'redacted text only'}</p>
    {(getToken||a.semantic_retrieval||a.classification)&&<NeuralTools analysis={a} getToken={getToken} previewText={turnSelection==='latest'?previewText:undefined}/>}
    {records.length>0&&<label>Inspect committed turn<select aria-label="Inspect committed turn" value={turnSelection} onChange={e=>{setTurnSelection(e.target.value);setSelected(null);}}><option value="latest">Current result</option>{records.map((r,i)=><option value={i} key={r.turn_id||i}>Turn {i+1}</option>)}</select></label>}
    <p>Strategy: <strong>{a.strategy}</strong> · {a.strategy_evidence.content_tokens} content tokens · {a.strategy_evidence.prior_topic_turns} previous topic turns</p>
    {a.parser_fallback && <p role="status">Sentence fallback: {a.parser_fallback}. Dependency relations are unavailable.</p>}
    <p className="redacted" data-testid="redacted">{boundaries.slice(0,-1).map((start,i) => { const end=boundaries[i+1]; return <span key={start} className={highlight.some(([x,y])=> start>=x && end<=y) ? 'span-highlight' : ''}>{a.redacted_text.slice(start,end)}</span>; })}</p>
    <h3>Explicit-connective relation graph</h3>
    <p>Select an arc to highlight its cue and arguments. Arrows show semantic direction; contrast is symmetric.</p>
    <svg className="clause-arcs" viewBox={`0 0 ${Math.max(480,a.clauses.length*140)} 180`} aria-label="Clause relation arcs">
      <defs><marker id="semantic-arrow" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto"><path d="M0,0 L0,6 L7,3 z" fill="currentColor"/></marker></defs>
      {a.relations.map((r,i) => { const x1=70+140*clauseIndex[r.source], x2=70+140*clauseIndex[r.target], h=28+i*18; return <g key={r.id} aria-label={`${r.cue} arc`} onClick={()=>setSelected(r.id)}><path d={`M${x1},140 Q${(x1+x2)/2},${h} ${x2},140`} fill="none" stroke="transparent" strokeWidth="18" style={{cursor:'pointer',pointerEvents:'stroke'}}/><path className={selected===r.id?'arc selected':'arc'} d={`M${x1},140 Q${(x1+x2)/2},${h} ${x2},140`} markerEnd={r.symmetric?undefined:'url(#semantic-arrow)'}/><text x={(x1+x2)/2} y={h+38} textAnchor="middle">{r.cue}</text></g>;})}
      {a.clauses.map((c,i)=><g key={c.id}><circle cx={70+i*140} cy="145" r="5"/><text x={70+i*140} y="168" textAnchor="middle">{c.id}</text></g>)}
    </svg>
    <div className="topic-cards">{a.relations.map(r=><button key={r.id} aria-pressed={selected===r.id} onClick={()=>setSelected(r.id)} aria-label={`Select ${r.cue} relation`}>{r.cue}: {r.arg1} / {r.arg2}</button>)}</div>
    {!a.relations.length && <p>No supported explicit connective found.</p>}
    <ol className="clauses">{a.clauses.map(c=><li key={c.id} className={edge&&(edge.arg1===c.id||edge.arg2===c.id)?'span-highlight':''}><strong>{c.id}</strong> {c.text}</li>)}</ol>
    {edge && <p data-testid="arguments">Arg1: {edge.arg1} · Arg2: {edge.arg2} · {edge.relation} · cue offsets [{edge.cue_span.join(', ')}]</p>}
    <h3>Lesk word senses</h3>
    {a.lesk?.status==='ready'?a.lesk.senses.map(s=><details key={s.span.join(':')}><summary>{s.lemma} → {s.selected.sense} · overlap {s.selected.score}</summary><p>{s.selected.definition}</p><ul>{s.candidates.map(c=><li key={c.sense}>{c.sense}: score {c.score}, evidence [{c.overlap.join(', ')}], animacy {c.animacy}</li>)}</ul></details>):<p>WordNet senses unavailable.</p>}
    <h3>Hobbs antecedent proposals</h3>
    <p>Constituency parser: {a.hobbs?.backend || 'unavailable'}. Number/person compatibility is checked; name gender remains unknown.</p>
    {a.hobbs?.limitation && <p role="status">{a.hobbs.limitation}</p>}
    {!a.hobbs?.pronouns?.length && <p>No antecedent proposals recorded. Missing or unresolved references are not filled in.</p>}
    {a.hobbs?.pronouns?.map(p=><details key={p.span.join(':')}><summary>{p.pronoun} → {p.antecedent || 'unresolved'}</summary><ol>{(p.candidates || []).map(c=><li key={c.entity}>{c.entity}: rank {c.rank}, distance {c.sentence_distance}, agreement {String(c.agreement)}</li>)}</ol></details>)}
    <h3>Centering transitions</h3>
    <p>Sentence units. Forward centers rank subject before objects; NO_CB means no shared backward center was found.</p>
    <table><thead><tr><th>Sentence</th><th>Cf</th><th>Cp</th><th>Cb</th><th>Transition</th></tr></thead><tbody>{a.centering?.trace?.map(c=><tr key={c.sentence}><td>{c.sentence+1}</td><td>{c.cf.join(', ')}</td><td>{c.cp || '—'}</td><td>{c.cb || '—'}</td><td>{c.transition}</td></tr>)}</tbody></table>
    <h3>DMRST discourse parsing</h3>
    {a.dmrst?.status==='ready'?<><p>Neural CPU inference · {a.dmrst.backend}</p><ol>{a.dmrst.edus.map(e=><li key={e.id}>EDU {e.id}: {e.text}</li>)}</ol><ul>{a.dmrst.tree.map((r,i)=><li key={i}>EDU {r.left.join('–')} ({r.left_nuclearity}) — {r.relation} — EDU {r.right.join('–')} ({r.right_nuclearity})</li>)}</ul></>:<p role="status">DMRST unavailable: {a.dmrst?.reason || 'not included in this historical record'}. No neural RST output has been substituted.</p>}
    <h3>Personal world memory</h3>
    <h4>Retrieved earlier scenes</h4>
    {a.memory_retrieval?.map(s=><blockquote key={s.scene_id}>{s.scene_id} · similarity {value(s.similarity ?? s.semantic_score ?? s.lexical_score)}<p>{s.excerpt || s.text}</p></blockquote>)}
    {a.pwm&&<><p>{a.pwm.entities.length} entities · {a.pwm.relationships.length} explicit co-mentions · {a.pwm.scenes.length} scenes · {a.pwm.threads.length} threads</p><details><summary>Relationships and scenes</summary><ul>{a.pwm.relationships.map((r,i)=><li key={i}>{r.entity_ids.join(' ↔ ')}: {r.type} ({r.scene_ids.length} scenes)</li>)}</ul>{a.pwm.scenes.map(s=><blockquote key={s.id}>{s.id} · {s.thread_id||'unassigned'}<p>{s.text}</p></blockquote>)}</details><details><summary>Threads</summary><ul>{a.pwm.threads.map(t=><li key={t.id}>{t.id}: {t.count} turns, activation {t.activation.toFixed(3)}, entities {t.entity_ids.join(', ')}</li>)}</ul></details><details><summary>Unresolved references and recurring language</summary><ul>{a.pwm.unresolved.map(u=><li key={u.id}>{u.id}: {u.type} · {u.status}</li>)}</ul>{a.pwm.private_language.map(p=><p key={p.phrase}>“{p.phrase}” — {p.count} occurrences</p>)}</details><p>{a.pwm.interpretation}</p></>}
    <h3>Topic memory</h3><p>Current topic: {a.topic_id || 'Unassigned'} · window entropy: {value(a.topic_entropy)}</p>
    <div className="topic-cards">{a.topics.map(t=><button key={t.id} onClick={()=>setTopic(topic===t.id?null:t.id)} aria-pressed={topic===t.id}>{t.id} · {t.count} turns</button>)}</div>
    <h3>Extractive turn summary</h3>
    {a.summary_turns.filter(t=>!topic||t.topic_id===topic).map(t=><blockquote key={t.turn_index}>Turn {t.turn_index} · {t.topic_id}<p>{t.text}</p></blockquote>)}
    <h3>Raw and filtered textual features</h3>
    <p>Blue: raw observation. Orange: filtered estimate. Covariance bands describe model uncertainty. Missing values stay unavailable.</p>
    <div className="feature-grid">{Object.keys(names).map((k,index)=><article key={k}><h4>{names[k]}</h4><p>Raw {value(a.features[k])} · filtered {a.posterior.initialized[index]?value(a.posterior.x[index]):'Unavailable'}</p><svg viewBox="0 0 300 110" aria-label={`${names[k]} timeline`}>
      {history.map((r,i)=>{const x=15+i*270/Math.max(1,history.length-1), p=r.posterior; const y=v=>95-Math.max(0,Math.min(1,v))*80; const estimate=p.x[index], raw=r.features[k]; return <g key={i}>{p.initialized[index]&&<><line x1={x} x2={x} y1={y(estimate+1.96*Math.sqrt(p.P[index][index]))} y2={y(estimate-1.96*Math.sqrt(p.P[index][index]))} stroke="#dca677"/><circle cx={x} cy={y(estimate)} r="3" fill="#ad4e24"/></>}{raw!=null&&<circle cx={x} cy={y(raw)} r="2" fill="#355f93"/>}</g>;})}
    </svg></article>)}</div>
    <BackendCoreDetails analysis={a}/>
  </section>;
}
