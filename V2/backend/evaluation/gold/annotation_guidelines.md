# Annotation Guidelines: Sanctuary V2 Discourse-Grounded Question Selection

## 1. Overview & Open-Vocabulary Principle
These guidelines specify the ground-truth annotation format for Sanctuary V2. Every turn is annotated strictly based on surface and discourse structure.
**Critical Rule**: The system never guesses user emotions, psychological states, or conversational intent from pre-defined affective lexicons. All commitments, gaps, and dialogue moves are derived from structural evidence: syntactic roles, dependency parse trees, discourse relations, modality operators, and coreference chains.

---

## 2. Unit of Annotation: Proposition Commitments
A **Commitment** is an active proposition asserted by the user. Each frame captures:
- `predicate`: The lemma of the governing verb or state predicate (e.g., `"get"`, `"feel"`, `"blame"`).
- `agent`: The syntactic agent or subject (in passive voice, the recovered by-agent; in active voice, the nsubj).
- `patient`: The syntactic patient or direct object (dobj, or passive nsubjpass).
- `polarity`: `"positive"` or `"negative"`.
  - *Negation scope*: Negation determiners (`"no one"`, `"never"`), neg adverbs (`"not"`), and double negation (`"can't not"`) must be resolved.
  - *Negation raising*: In `"I don't think I'm angry"`, negation is scoped to `"angry"`, marking `"angry"` as negative polarity.
- `modality`: `"asserted"` (factual occurrence), `"obligation"` (`"should"`, `"must"`), `"counterfactual"` (`"would have"`), or `"tentative"` (`"might"`, `"could"`).
- `hedge`: Boolean (`true` if modified by epistemic markers such as `"I think"`, `"maybe"`, `"I guess"`, `"honestly"`, `"kind of"`).
- `span`: `[start, end]` exact half-open character offsets in the user utterance.

---

## 3. Discourse Relations
Annotate explicitly signaled or syntactically bound coherence relations between clauses:
- `causal`: Cause-effect relations. Explicit connectives include `"because"`, `"since"`, `"that's why"`, `"which is why"`. Non-clausal or verbal causatives include `"made me"`, `"led to"`.
  - *Hard negative*: Two juxtaposed sentences with no explicit or structurally entailed edge (`"I left. He was loud."`) have NO causal edge.
- `contrast`: Adversative relations. Explicit markers include `"but"`, `"however"`, sentence-final `"though"`, `"nothing but"`, `"all but"`.
- `temporal`: Succession or simultaneity (`"before"`, `"after"`, `"while"`).

---

## 4. Corrections and Supersession
- `is_correction`: `true` only if the user explicitly repairs, retracts, or overrides a prior claim.
- Cues: `"no wait"`, `"I meant"`, `"actually it was"`, `"scratch that"`, Hinglish `"nahi, matlab"`.
- *Hard negative*: `"actually"` used as an emphatic filler (`"Actually, I like it"`) is NOT a correction. `"No, I don't want to talk about that"` is a conversational rejection, NOT an epistemic correction.
- Target: Identifies the earlier frame or entity superseded. If ambiguous, marked `"unresolved"`.

---

## 5. References and Pronouns
- Each pronoun (`"he"`, `"she"`, `"they"`, `"it"`) is evaluated for antecedent in the turn or discourse state:
  - `"resolved"`: Unambiguous single antecedent.
  - `"ambiguous"`: Multiple grammatical candidates with equal agreement (e.g., `"my mom told my sister she was wrong"`).
  - `"unresolved"`: Zero nominal evidence in prior context.

---

## 6. Structural Gaps (The 8 Canonical Types)
A **Gap** is an open structural site in the user's discourse that licenses elaboration:
1. `unfilled_role`: Eventive predicate lacking an expected argument (no stated cause, result, instrument, or temporal frame where relevant).
2. `hedged_commitment`: An assertion weakened by an epistemic hedge (`"I guess..."`) without explanation.
3. `reported_claim`: Reported speech/event from an external agent (`"She said..."`) where the user has stated no evaluation.
4. `unresolved_reference`: A pronoun or referring expression with ambiguous or absent antecedents.
5. `correction_link`: A correction cue whose exact target predicate is ambiguous.
6. `counterfactual_obligation`: An unfulfilled obligation (`"I should have..."`) or counterfactual without further development.
7. `contrast_thin_arm`: A contrast where one side has descriptive elaboration and the other side is undeveloped (`"On one hand X... but on the other Y."`).
8. `recurring_topic`: A topic mentioned across multiple turns without a stated resolution.

*Hard Negatives*: Complete logistical or factual narration (`"I submitted the form on Monday"`) contains ZERO gaps.

---

## 7. Acceptable Dialogue Moves
- `ask`: Valid only when at least one verified structural gap exists with eligible commitments within the presupposition budget.
- `clarify`: Valid when an unresolved reference or ambiguous correction blocks understanding.
- `acknowledge`: Valid when user presents a complete narrative, a plan, or when venting without wanting interrogation.
- `hold`: Valid when turn is very short (`"ok"`, `"hm"`), when user explicitly requests silence (`"just let me talk"`), or when question budget is exhausted.
