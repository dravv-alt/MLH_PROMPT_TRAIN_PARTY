# Sanctuary V2 Canonical Scope: Discourse-Grounded Question Selection

## Target Scope
- **Active Codebase Scope**: `V2/backend` ONLY.
- **Untouched Directories**: `V1_MVP/`, `sanctuary_v2/`, and root legacy scripts are frozen/untouched.

## 1. Goal, Thesis, and Non-Goals
- **Goal**: Make the NLP stack the decision-maker in every turn: it finds what is open, unsaid or unresolved in the user's own discourse, decides whether to ask and what, checks that a question presupposes only what the user said, and shows the user why.
- **Thesis (falsifiable)**: Questions chosen from open-vocabulary discourse gaps and filtered for licensed presuppositions help users elaborate and clarify more, and feel less forced, than LLM-only replies or restatement, on two different local models. No emotion, topic or intent label is assumed in advance.
- **Non-goals**:
  - Beating frontier models on fluency.
  - Any psychological-state inference.
  - Clinical claims.
  - Preset emotion, topic or intent taxonomies.
  - Restating the conversation back to the user as the main reply.
  - New endpoints beyond extending `/chat` and `/nlp/analyze` payloads.
  - Fine-tuning/LoRA.
  - Decode-time token masking is an optional experiment, not on the critical path.
- **Success Definition**: The ablation matrix in Phase 6 shows a measured effect with a stated mechanism per row, the LLM-off path still gives a traced diagnostic view and a valid reply, and every limit is reported.

## 2. Open-Vocabulary Principle
The system never decides in advance what the user feels, what the conversation is about, or what kind of help they want. Every gap, question target, and move is derived from the structure of the user's own text (frames, relations, hedges, references, modality, topic history) and traces to spans. Where the structure shows nothing worth asking, the correct move is a brief acknowledgment or no question.

## 3. Global Rules & Invariants
1. **Evidence before "done"**: Files and line ranges changed, exact test commands, raw output, hard-negative results.
2. **Freeze before measuring**: Metric definitions, thresholds, and test split frozen in T0.2/T0.3 before system results.
3. **Dev/test separation**: Existing 80 dev turns annotated; fresh 40-turn held-out test set written in T0.2 and untouched until Phase 6.
4. **Hard negatives are first-class**: Every task ships with negative inputs designed to expose failure modes.
5. **Minimal surface**: SQLite stays the only store; fields added to existing payloads.
6. **Standing invariants**:
   - Privacy canary: seeded PII strings never appear in DB rows, logs, or exports.
   - LLM-off path returns a valid reply and diagnostic view.
   - Analysis is deterministic for a fixed input and seed.
   - p95 latency within frozen budget.
7. **No hardcoded affect, topic, or intent**: Zero sentiment/emotion dictionaries driving decisions. Closed-class function words permitted.
