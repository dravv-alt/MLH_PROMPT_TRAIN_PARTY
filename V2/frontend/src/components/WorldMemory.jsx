import {useState} from 'react';

export default function WorldMemory({memory,graph,onReview}) {
  const [selected,setSelected]=useState(null);
  if(!memory||!graph)return null;
  const nodes=graph.nodes || [], edges=graph.edges || [];
  const columns=[...new Set(nodes.map(n=>n.type))].sort();
  const positions={};
  columns.forEach((kind,column)=>nodes.filter(n=>n.type===kind).forEach((n,i)=>{positions[n.id]={x:90+column*260,y:65+i*42};}));
  const height=Math.max(150,...Object.values(positions).map(p=>p.y+30)), width=Math.max(900,columns.length*260);
  const incident=edges.filter(e=>e.source===selected||e.target===selected);
  const node=nodes.find(n=>n.id===selected);
  return <section className="nlp-panel"><h2>Memory connections</h2><p>Revision {memory.revision}. Select a node to inspect evidence. Co-mention edges do not infer personal relationships.</p>
    {!nodes.length&&<p>No committed memory yet.</p>}
    <div className="memory-graph-scroll"><svg viewBox={`0 0 ${width} ${height}`} style={{width,minWidth:width}} aria-label="World memory graph">
      {columns.map((kind,i)=><text key={kind} x={90+i*260} y="25" fontSize="14">{kind.replaceAll('_',' ')}</text>)}
      {edges.map((e,i)=>{const a=positions[e.source],b=positions[e.target];return a&&b?<line key={i} x1={a.x} y1={a.y} x2={b.x} y2={b.y} stroke={e.source===selected||e.target===selected?'#a24f26':'#bdbdbd'}/>:null;})}
      {nodes.map(n=><g key={n.id} onClick={()=>setSelected(n.id)} style={{cursor:'pointer'}}><circle cx={positions[n.id].x} cy={positions[n.id].y} r="7" fill={n.id===selected?'#a24f26':'#456c88'}/><text x={positions[n.id].x+12} y={positions[n.id].y+4} fontSize="11">{String(n.label || n.id).slice(0,32)}</text></g>)}
    </svg></div>
    <details><summary>Choose from all {nodes.length} nodes</summary><div className="topic-cards">{nodes.map(n=><button key={n.id} onClick={()=>setSelected(n.id)} aria-pressed={selected===n.id}>{n.label || n.id}</button>)}</div></details>
    {node&&<article><h3>{node.label || node.id}</h3>{node.text&&<p>{node.text}</p>}<ul>{incident.map((e,i)=><li key={i}>{e.source} → {e.target}: {e.type}; evidence {(e.evidence_scene_ids||[e.evidence_scene_id]).filter(Boolean).join(', ') || 'See source record'}</li>)}</ul></article>}
    {onReview&&<><h3>Unresolved reference review</h3>{(memory.unresolved||[]).map(u=><article key={u.id}><p>{u.id}: {u.type} · {u.status}</p><div className="topic-cards">{['open','acknowledged','dismissed'].map(status=><button key={status} disabled={u.status===status} onClick={()=>onReview(u.id,status)}>{status}</button>)}</div></article>)}</>}
  </section>;
}
