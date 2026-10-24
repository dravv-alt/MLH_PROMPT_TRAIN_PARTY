// Older saved turns legitimately lack newer modules. Do not invent their output.
export function analysisRecord(source) {
  if (!source) return null;
  const result = {...source};
  for(const key of ['clauses','relations','mentions','topics','summary_turns']) {
    result[key] = Array.isArray(source[key]) ? source[key] : [];
  }
  result.features = source.features || {};
  result.strategy_evidence = source.strategy_evidence || {};
  result.redacted_text = source.redacted_text || '';
  result.posterior = {initialized:[], x:[], P:[], ...source.posterior};
  return result;
}
