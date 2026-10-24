// Status reflects this record, not merely the existence of source code.
export function algorithmCatalog(a = {}) {
  const m = a.mathematical_models || {};
  const row = (id, name, value, role, note = '') => ({id, name, value, role, note,
    status: value == null ? 'not recorded' : value.status || 'recorded'});
  return [
    row('privacy', 'PII detection and anonymous entities', a.mentions, 'Canonical text and entity matching'),
    row('clauses', 'spaCy dependencies and clause segmentation', a.clauses, 'Discourse arguments', a.parser_fallback || ''),
    row('connectives', 'Explicit-connective relation graph', a.relations, 'Relations and strategy; not a full RST tree'),
    row('lesk', 'Lesk / WordNet', a.lesk, 'Lexical senses and compatibility'),
    row('hobbs', 'Hobbs antecedent proposals', a.hobbs, 'Reference candidates', a.hobbs?.limitation || ''),
    row('centering', 'Restricted Centering', a.centering, 'Entity focus and continuity'),
    row('dmrst', 'DMRST neural discourse parser', a.dmrst, 'EDUs, relations and nuclearity'),
    row('topics', 'Lexical / MiniLM topic assignment', a.topic_assignment, 'Topic and recurring strategy'),
    row('entropy', 'Shannon topic entropy', a.topic_entropy, 'Recent topic distribution; missing with insufficient evidence'),
    row('lexrank', 'LexRank extractive turn summary', a.summary_turns, 'Representative user turns'),
    row('kalman', 'Four-feature online Kalman filter', a.posterior, 'Textual features, not psychological measurements'),
    ...Object.entries(m.filters || {}).map(([key, value]) => row(key, key.replaceAll('_', ' '), value, 'Experimental comparison, not response selection')),
    row('hmm', 'HMM + Viterbi', m.hmm, 'Experimental sequence-state diagnostics'),
    row('crf', 'CRF-form clause decoder', m.crf, 'Fixed-score structured decoder, not a trained CRF'),
    row('belief', 'Bayesian / Dempster–Shafer / revision ledger', m.evidence_belief_revision, 'Experimental evidence bookkeeping'),
    row('graph', 'Temporal Narrative Graph', m.temporal_narrative_graph, 'Explicit temporal, relation and revision links'),
    row('calibration', 'Temperature calibration', m.confidence_calibration, 'Requires labelled development data'),
    row('maxent', 'MaxEnt revision classifier', a.revision_classifier, 'Advisory correction, uncertainty and preference labels'),
    row('ssm', 'Six-layer Situational Structure Model', a.situational_structure, 'Conservative lexical structure', a.ssm_metadata?.method),
    row('pwm', 'Personal World Model', a.pwm, 'Entities, scenes, threads and unresolved references'),
    row('retrieval', 'MiniLM window cosine + RRF', a.semantic_retrieval, 'Exploratory hybrid memory retrieval'),
    row('nli', 'DeBERTa zero-shot NLI', a.classification, 'Async suggestions; never response strategy'),
    row('memory', 'Evidence-linked memory harness', a.context_packet, 'Correction-aware context selection'),
    row('discourse', 'Restricted DRT/SDRT-inspired frames', a.discourse_context, 'Actors, negation, modality and revision scope'),
    row('generation', 'Response planner, Transformer and validators', a.generation, 'Validated generation or labelled fallback'),
  ];
}
