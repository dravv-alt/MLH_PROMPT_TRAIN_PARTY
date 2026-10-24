const pretty = value => JSON.stringify(value, null, 2);
const label = value => value.replaceAll('_', ' ');
const number = value => typeof value === 'number' ? value.toFixed(4) : 'Unavailable';

export default function BackendCoreDetails({analysis:a}) {
  if(!a)return null;
  const packet=a.context_packet, math=a.mathematical_models, plan=a.response_plan;
  return <section className="backend-core">
    <h3>How memory shaped this turn</h3>
    {!packet?<p>Memory evidence was not recorded for this turn.</p>:<>
      <p>{packet.abstained_from_history?'No eligible earlier evidence selected.':`${packet.relevant_prior_evidence?.length || 0} earlier evidence items selected.`}</p>
      {packet.relevant_prior_evidence?.map(row=><article className="evidence-card" key={row.assertion_id}><blockquote>{row.text}</blockquote><p>Turn {row.source_turn_index} · {row.epistemic_status} · {row.revision_status}</p><p>Selected by {(row.selection_routes||[]).join(', ')}</p></article>)}
      <details><summary>Corrections, supersessions and unresolved evidence</summary><pre>{pretty({corrections:packet.corrections_and_supersessions,unresolved:packet.unresolved_conflicts,retrieval_trace:packet.retrieval_trace,update:a.memory_update})}</pre></details>
    </>}
    <h3>Six-layer situational structure</h3>
    <p>Extracted textual structure; unknown fields remain unavailable.</p>
    {a.situational_structure?Object.entries(a.situational_structure).map(([key,value])=><details key={key}><summary>{label(key)}</summary><pre>{pretty(value)}</pre></details>):<p>Not recorded in this historical turn.</p>}
    <h3>Mathematical models</h3><p>These estimates describe textual features. They are not psychological measurements.</p>
    {math?.filters?<div className="feature-grid">{Object.entries(math.filters).map(([key,filter])=><article className="evidence-card" key={key}><h4>{label(key)}</h4><dl>{(math.dimensions||[]).map((dimension,i)=><div key={dimension}><dt>{label(dimension)}</dt><dd>{filter.initialized?.[i]?number(filter.estimate?.[i]):'Unavailable'} {filter.observation_mask?.[i]?'':'(no observation)'}</dd></div>)}</dl><details><summary>Covariance and latent values</summary><pre>{pretty(filter)}</pre></details></article>)}</div>:<p>No mathematical suite recorded.</p>}
    {math&&<details><summary>HMM, Viterbi, clause decoding and belief ledger</summary><pre>{pretty({hmm:math.hmm,crf:math.crf,evidence_belief_revision:math.evidence_belief_revision,temporal_narrative_graph:math.temporal_narrative_graph,calibration:math.confidence_calibration})}</pre></details>}
    <h3>Response planning and generation</h3>
    {plan?<><p>Strategy: {plan.strategy}. Intent: {plan.intent}.</p><ol>{plan.claims_to_communicate?.map(c=><li key={c.id}>{c.text} <small>({c.epistemic_status})</small></li>)}</ol><details><summary>Actors, negation, modality and revision scope</summary><pre>{pretty({propositions:plan.proposition_frames,revision_links:plan.revision_links,corrections:plan.correction_context,explicit_relations:plan.required_semantic_relations})}</pre></details></>:<p>No response was generated for this preview.</p>}
    {a.generation&&<details><summary>Generation attempts and validation</summary><p>{a.generation.mode} · {a.generation.status}</p><pre>{pretty(a.generation)}</pre></details>}
    <details><summary>Complete backend record</summary><pre>{pretty(a)}</pre></details>
  </section>;
}
