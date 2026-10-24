"""Render inspected API responses and algorithm attribution from an evaluation."""
import argparse
import json
from collections import Counter
from pathlib import Path


def report(path):
    data = json.loads(path.read_text(encoding='utf-8'))
    rows = data['records']
    counts = Counter()
    for row in rows:
        policy = row.get('policy') or {}
        counts.update(policy.get('plan', {}).get('violations', []))
        counts.update(policy.get('semantic', {}).get('violations', []))
        semantic = policy.get('semantic', {})
        if semantic.get('status') == 'unavailable':
            counts['semantic_unavailable:' + semantic.get('reason', 'unknown')] += 1
    historical = [r for r in rows if r['memory'].get('historical_excerpt_count_sent', 0)]
    lines = [
        '# Sanctuary hosted evaluation and NLP contribution report', '',
        'Date: 17 October 2026. This describes the actual evaluation path, with source-level attribution; it does not assign invented percentage contributions to algorithms.', '',
        f"Model: `{data['contract'].get('hosted_model')}` through Groq.",
        'Run configuration: temperature 0.3; temporary API output allowance 512 tokens; minimum 1.5 seconds after the previous wrapper call; at most five attempts on empty/error outcomes. Environment overrides applied only to the evaluation process.',
        f"Turns: {len(rows)} across {len(set(r['topic_id'] for r in rows))} conversations.",
        f"Accepted: {data['summary']['accepted']}/{len(rows)} ({100 * data['summary']['accepted']/len(rows):.2f}%).",
        f"Rejected: {data['summary']['validator_rejected']}. Provider unavailable: {data['summary']['provider_unavailable']}. Fallback results: zero.",
        f"Runtime: {data['summary']['runtime_seconds']:.1f}s. Mean wrapper-call latency: {data['summary']['mean_provider_call_seconds']}s.",
        f"Turns actually sent earlier memory excerpts: {len(historical)}. First turns naturally have no history; retrieval may also abstain on later turns.", '',
        f"Wrapper attempts returning no visible completion: {sum(not a['received'] for r in rows for a in r['attempts'])}. Turns needing retries: {sum(len(r['attempts']) > 1 for r in rows)}. Empty/error outcomes are combined by the legacy provider wrapper.",
        f"Detected-surface leaks recorded after the outgoing privacy check: {sum(r.get('privacy', {}).get('detected_surface_leak_count', 0) for r in rows)}. Outputs with unresolved entity tokens: {sum(bool(r.get('privacy', {}).get('unresolved_placeholders')) for r in rows)}. Known placeholder occurrences restored locally: {sum(r.get('privacy', {}).get('restored_placeholder_count', 0) for r in rows)}.", '',
        f"Accepted drafts with at least one false lexical/kind coverage diagnostic: {sum(r['status']=='accepted' and not all((r.get('policy') or {}).get('plan', {}).get('required_claim_coverage', {}).values()) for r in rows)}. This is a diagnostic count, not an adjudicated omission count; the checker can miss paraphrases.", '',
        '## What happens to an input', '',
        'Original input → local spaCy/regex redaction → dependency analysis and clauses → proposition frames and canonical memory update → active evidence retrieval → response plan → classical source reflection + approved claims + up to three historical excerpts → API Transformer wording → local rule validators → local NLI semantic gate → local placeholder restoration for display.', '',
        'A provider draft rejected by validation is retained as a rejected evaluation draft. It is not a safe response to ship. Provider errors/empty completions receive bounded retries; validation rejections are measured without substituting the classical source reflection.', '',
        '## Algorithm-to-output attribution', '',
        '| Algorithm/component | Concrete computation | Contribution in this run | Source |',
        '|---|---|---|---|',
        '| spaCy NER + regex | Detects PERSON/ORG/place and contact/date patterns; replaces detected spans with stable entity IDs | Directly changes every provider-bound textual representation and supports local restoration | `app/services/nlp_engine.py:redact` |',
        '| Unicode canonicalization + keyed alias hashing | Matches normalized entity aliases across turns without storing original names in state | Preserves identity continuity and stable placeholder references | `nlp_engine.py:canonical, alias_hash, redact` |',
        '| spaCy tokenization, POS, lemmatization, dependencies | Produces tokens, lexical lemmas and syntactic roles | Feeds clause structure, lexical retrieval, features and propositions | `nlp_engine.py:pipeline, parse` |',
        '| Dependency clause segmentation | Root/advcl/ccomp/relcl/parataxis/verbal conjunction heads; ordered discontiguous spans | Defines proposition evidence and explicit relation arguments | `nlp_engine.py:clause_graph` |',
        '| Explicit-connective rules | Cue/dependency/POS tests for cause, condition, contrast, temporal and elaboration links | Affects strategy and memory graph edges; raw graph is not sent to this polish prompt | `nlp_engine.py:clause_graph` |',
        '| Hashed term-frequency vectors + cosine | 16,384 nonnegative dimensions, unit weighting, normalized sparse vectors | Supplies lexical topics, prior-scene retrieval and novelty; this is not TF-IDF | `nlp_engine.py:vector, cosine, analyze_turn` |',
        '| Online leader topic clustering | Thresholded centroid assignment with deterministic ties | Supplies local topic/thread continuity; order-dependent | `nlp_engine.py:analyze_turn`, `pwm.py:update_world` |',
        '| PWM world memory | Turn scenes, co-mentioned entities, thread centroid sums and lexical phrase recurrence | Holds source scenes and thread structure used around canonical retrieval | `pwm.py:update_world` |',
        '| Restricted DRT/SDRT-inspired frames | Predicate, grammatical actors, negation, modality, scope spans | Direct input to canonical assertions and revision handling; not a full DRT/SDRT formalism | `discourse_context.py:build_discourse_context` |',
        '| Canonical memory and scoped belief revision | Assertion/evidence IDs, correction matching, supersession/refinement/conflict handling | Controls which prior claims remain eligible; does not guarantee perfect correction interpretation | `memory_harness.py:propose_update` |',
        '| Bounded evidence retrieval | Lexical overlap, graph links, topic routes and recency ranking; status exclusion and per-turn diversity | Directly selects the earlier excerpts seen by the API | `memory_harness.py:_candidate_routes, retrieve` |',
        '| Deterministic response planner | Selects up to three current text claims, preserves tentative/rejected status, attaches memory | Sets the current factual material to verbalize | `response_planner.py:build_response_plan` |',
        '| Classical realization and pronoun conversion | Converts selected current claims to second-person reflection | Supplies the API rewrite source; it is never used as a replacement result in this test | `response_planner.py:realize_plan_classically`, `local_generation.py:repair_second_person_voice` |',
        '| Hosted autoregressive Transformer | Generates new wording conditioned on the supplied text | Produces all 80 API drafts; this is the component responsible for surface fluency and much of sentence composition | `groq_client.py:GroqReflector.generate` |',
        '| Rule-based output validation | Advice/question/diagnosis/meta/voice/length checks, tentative hedging and correction checks | Accepts/rejects drafts; does not generate them | `response_planner.py:validate_plan_response`, `response_policy.py` |',
        '| Local DeBERTa NLI | Three-way entailment/neutral/contradiction comparisons: evidence→draft, draft→claim, correction consistency | Semantic acceptance gate for structurally valid drafts; scores are uncalibrated | `response_semantics.py:evaluate_candidates` |',
        '| Placeholder restoration | Exact lookup of returned known entity tokens in topic-local mapping | Restores original identities after local validation; mappings stay local | `privacy.py:restore_identifiers` |', '',
        '## Computed components that do not directly word this API prompt', '',
        '| Component | What it does | Actual boundary |',
        '|---|---|---|',
        '| Simplified Lesk + WordNet | Ranks senses by gloss/example/context set overlap | Analysis output; can aid the classical reference module. No senses are supplied in the API prompt |',
        '| Hobbs-style proposals + restricted Centering | Constituency antecedent proposal order and entity-transition traces | Analysis/PWM unresolved-reference support. No claim of complete coreference resolution or direct API conditioning |',
        '| DMRST neural discourse parser | EDU segmentation and discourse tree when resources are available | Called by analyzer; its tree is not consumed by this hosted polish prompt |',
        '| PhraseMatcher hedge density | Counts longest non-overlapping hedge phrases per lexical token | Feeds feature timelines; selected-claim uncertainty also has separate rule checks |',
        '| Entity continuity/connective density/topic novelty | Defined numerical textual features | Inputs to numerical filters; no direct effect on API wording |',
        '| Linear KF, EKF, UKF, EnKF and particle filter | Estimates four textual feature dimensions with different update equations | Experimental numerical enrichment. No filtered state is sent to the API |',
        '| HMM + Viterbi | Fixed heuristic emissions and transitions for narrative phase sequence | Diagnostic phase estimate; no trained state-accuracy claim or direct prompt use |',
        '| CRF-form Viterbi decoder | Fixed clause-label unary and transition potentials | Heuristic diagnostic labels, not a trained CRF used to generate responses |',
        '| Dempster–Shafer/evidence ledger and temporal narrative graph | Experimental evidence/status and graph summaries | Ledger informs plan restrictions locally; these raw objects are not in the API prompt. Not all restrictions are included as prompt text |',
        '| Shannon topic entropy | Last-window normalized assignment entropy | Diversity diagnostic; no direct prompt use |',
        '| LexRank-style PageRank | Weighted cosine turn graph and topic-diverse representative turns | Extractive summary diagnostic; representatives are not sent by this evaluator |',
        '| MaxEnt/logistic revision classifier | Small learned revision/function signal | Analyzer diagnostic; canonical correction decisions do not directly consume this prediction |',
        '| SSM six layers | Conservative typed event/constraint/reaction/meaning/temporal/language extraction | Attached to the response plan but not read by this API prompt builder |',
        '| MiniLM semantic topics and RRF dense retrieval | Available in application service enrichment | This evaluator calls analyze_turn directly and does not call NLPService.enrich/apply_semantic_topic_assignment. Therefore this test does not exercise MiniLM/RRF |',
        '| Asynchronous 13-label NLI classification | Experimental topic/function suggestions | Not invoked by this evaluator and never drives generation strategy |', '',
        'No algorithm-specific improvement can be measured from this run alone: that requires controlled ablations and human relevance/fidelity judgments. Validator acceptance is not human-quality accuracy. Earlier estimates that 80–90% of the NLP remained local were informal architectural estimates, not measured contributions; no defensible percentage of response quality can be assigned to a module here.',
        'The earlier local 24-turn polish acceptance (2/24) and this hosted 80-turn result have different sample sizes and generation paths. Do not interpret their raw rates as a controlled provider superiority experiment.', '',
        '## Verification performed', '',
        'Four focused tests passed in `tests/test_hosted_memory_evaluation.py`: (1) real analysis/canonical memory passes prior evidence to the second-turn provider prompt while a synthetic detected name remains local and restores through its placeholder; (2) unavailable transport leaves a null result rather than substituting classical text; (3) retry count, exponential delays and minimum spacing; (4) history excerpt count/length bounds and gold-free prompt construction.',
        'Transport and NLI responses were mocked in these boundary tests; DMRST and the constituency/reference parser were also mocked to keep the tests focused. The actual hosted run uses the real provider and local NLI worker. Python compilation passed for the evaluator and report generator. No full application test-suite or browser claim is made.', '',
        '## Mathematical interpretation', '',
        '- Hashed retrieval uses cosine: dot(a,b)/(norm(a) norm(b)). Unit weighting retains a fixed vector space across turns. Hash collisions and lexical mismatch remain limitations.',
        '- Leader topics assign a vector to its closest eligible centroid above 0.55 in the lexical analyzer; otherwise they create a topic. Short/zero vectors remain unassigned. MiniLM semantic assignment is a different application path, not exercised here.',
        '- Explicit-connective density = participating clauses / all clauses. Hedge density = non-overlapping matched phrases / lexical tokens. Entity continuity = repeated current entity IDs / current distinct IDs. Novelty = 1 − largest prior eligible cosine. Missing observations remain missing.',
        '- Linear Kalman update: x_pred=F x, P_pred=F P F^T+Q; K=P_pred H^T (H P_pred H^T+R)^−1; x=x_pred+K(z−H x_pred). Joseph covariance preserves numerical stability. With identity/diagonal structure these are independent scalar filters and resemble adaptive EMAs; they estimate textual features, not mental states.',
        '- EKF linearizes nonlinear observations with a Jacobian. UKF propagates sigma points with alpha=0.3, beta=2, kappa=0 in the balanced configuration. EnKF uses 32 ensemble members; the particle filter uses 128 particles and effective-sample-size resampling. These alternative filters are diagnostic in this generation route.',
        '- HMM filtering uses posterior proportional to emission × transition-predicted prior; Viterbi returns a maximum-score state path. Both the HMM emissions and CRF-form clause potentials are hand-set engineering choices.',
        '- Evidence bookkeeping uses Beta counts (mean alpha/(alpha+beta)) and Dempster–Shafer support/refutation/unknown mass combination. These are configured bookkeeping values, not evidence-calibrated probabilities.',
        '- Topic entropy is −sum(p log p)/log(K), undefined without at least two represented topics. LexRank uses weighted cosine PageRank with damping 0.85. Neither value reaches this API prompt.',
        '- NLI computes three-class softmax outputs independently per evidence/hypothesis pair. Strongest neutral evidence-support rejects as unsupported; strongest contradiction rejects the relevant semantic comparisons. This gate can make errors in either direction.', '',
        '## Privacy and context evidence', '',
        'Only redacted model data is passed into provider_prompt. Original-to-placeholder mappings remain local to one topic. The evaluator now fails before transmission if any surface detected by its redactor remains in the outgoing prompt. This verifies identified surfaces; NER may miss identities, so complete anonymization is not established.',
        'Known returned placeholders are restored locally after validation. Unknown placeholders are recorded as unresolved. The current tone validator flags any placeholder in the raw draft before restoration, so a restored known identity can still be marked rejected by that earlier gate. The synthetic boundary test verifies round-trip restoration but does not establish that such a response passes the full acceptance path. This ordering is a remaining integration limitation, not evidence of a failed lookup.',
        'The downloadable report keeps provider-side redacted text, avoiding an identity-bearing report; restored strings exist only in process. This isolated evaluator does not install restoration into the production /chat or TUI path.',
        'The eight dataset topics have separate state. Earlier assistant drafts are not promoted into user evidence. Up to three selected active prior excerpts, each at most 300 characters, reach the API. Superseded evidence is excluded by the harness. This supports bounded continuity, not complete-history recall.', '',
        'The earlier file `hosted_memory_harness_80_gptoss20b_20261017.json` is preserved as a flawed baseline: a wrong field lookup omitted all provider-bound history. It completed 80 turns with 37 accepted, 43 rejected and zero unavailable responses. Use the corrected run for continuity review. Sampling is enabled, so a rate difference cannot be attributed solely to context.', '',
        '## Manual reading and remaining defects', '',
        'In the corrected run, the achievement conversation showed real prior-context delivery: the sixth draft referred back to enjoying the achievement and continuing preparation. This is attributable to retrieved text being present in the prompt; it does not prove that every retrieved statement was still appropriate to repeat.',
        'The same conversation exposed important errors. Turn 2 weakened a tentative explanation into a stronger claim and was rejected by the hedging check. Turn 4 was rejected by semantic support despite a plausible paraphrase; this needs adjudication before calling it a validator false positive. Turn 8 ended with the incomplete phrase “a bigger part of” and was marked accepted. The existing word/sentence and NLI checks therefore do not establish grammatical completeness.',
        'An accepted actor error also occurred in conflict_interpretation_and_changing_understanding, turn 6: the input said “They later pointed out that one section was confusing”, but the output said “You mentioned that one section was confusing”. The API changed who made the observation, and local NLI did not reject it. Actor frames exist locally but are not sent to this polish prompt or checked by an explicit actor-alignment validator. This is a concrete missing connection between the NLP representation and output fidelity.',
        'Claim coverage also has an enforcement gap: validate_plan_response computes required_claim_coverage booleans but does not append a violation for a false value. The NLI claim-coverage branch rejects contradiction but does not reject neutral/missing entailment. Consequently an accepted draft may omit a required fact; the current acceptance label is weaker than complete claim preservation. This evaluation preserved those existing checks rather than silently changing its gate mid-run.',
        'The memory_consent scenario also illustrates an application boundary: the evaluator reflects requests about saving and deleting; it does not execute journal or memory-consent actions. An accepted sentence about keeping a short version is not evidence that anything was saved. The evaluator writes no application records.',
        'Other examples show the mixed quality of the hosted output. The final setback conversation, turn 9, cleanly preserved disappointment, reduced certainty about broad ability, and a preference to inspect individual mistakes. In contrast, boundaries_and_personal_agency turn 7 added a link between enjoying helping and being surprised by the emotions, although that causal connection was not explicitly established. Ambivalence turn 4 linked saying no to learning something new with an awkward “especially if” construction. Accepted outputs are often fluent paraphrases, but this is not yet consistently reliable, deeper reflection.',
        'The available reasoning model can spend its output allowance on hidden reasoning, leaving little visible text. This run used a 512-token cap; finish_reason and reasoning-token usage are not exposed by the legacy wrapper. Empty responses are retried, but nonempty truncated drafts are not transport errors and may pass existing validators. A follow-up should retain finish_reason/usage and reject or regenerate length-terminated/incomplete outputs without relaxing policy.',
        'Restoration can replace only a placeholder the model retains. When the model substitutes a generic phrase or invents a replacement identity, the original mapping cannot recover the intended reference. Named-input acceptance and production display integration require additional work.',
        'The API client currently collapses provider exceptions into an empty result, so retry counts are available but exact HTTP error categories and Retry-After are not. The minimum call spacing applies to wrapper calls; its SDK retries/HTTP transport retry may issue additional requests internally.', '',
        '## Rejection counts', '',
    ]
    lines.extend(f'- `{key}`: {value}' for key, value in counts.most_common())
    lines += ['', 'These counts can overlap on one turn. Semantic validation runs only after structural checks pass.', '', '## Per-conversation results', '', '| Conversation | Accepted | Rejected | Unavailable | Turns with history |', '|---|---:|---:|---:|---:|']
    for topic in dict.fromkeys(r['topic_id'] for r in rows):
        subset = [r for r in rows if r['topic_id'] == topic]
        lines.append(f"| {topic} | {sum(r['status']=='accepted' for r in subset)} | {sum(r['status']=='rejected_by_local_validators' for r in subset)} | {sum(r['status']=='provider_unavailable_after_retries' for r in subset)} | {sum(bool(r['memory'].get('historical_excerpt_count_sent')) for r in subset)} |")
    lines += ['', '## All input/output pairs', '', 'Rejected rows below are diagnostic drafts and were not approved for delivery.', '']
    for row in rows:
        lines += [f"### {row['topic_id']} — turn {row['turn_id']}", '', f"User (redacted): {row['redacted_input']}", '', f"API draft (redacted): {row['provider_response_redacted'] or '[unavailable]'}", '', f"Status: `{row['status']}`. Prior excerpts sent: {row['memory'].get('historical_excerpt_count_sent', 0)}.", '']
        policy = row.get('policy') or {}
        violations = policy.get('plan', {}).get('violations', []) + policy.get('semantic', {}).get('violations', [])
        if violations:
            lines += ['Violations: ' + ', '.join(f'`{v}`' for v in violations), '']
    target = path.with_suffix('.md')
    target.write_text('\n'.join(lines), encoding='utf-8')
    print(target)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('path', type=Path)
    report(parser.parse_args().path)
