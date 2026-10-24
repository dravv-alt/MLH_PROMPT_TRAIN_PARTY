# Sanctuary V2 Frozen Evaluation Metrics & Thresholds

Pre-registered and frozen as part of Task T0.3 prior to any baseline executions (T0.4).

## 1. Proposition-Level and Connective Metrics (NLP & Discourse Stack)
| ID | Metric Name | Definition | Target Threshold | Hard Floor |
|---|---|---|---|---|
| M1 | **Unlicensed-Connective Rate** | Fraction of reply connectives (causal/contrast) lacking explicit/syntactic edge in user utterance. | **0.00** | **<= 0.05** |
| M2 | **Polarity-Flip Rate** | Fraction of shared predicates where reply polarity contradicts user commitment. | **0.00** | **<= 0.02** |
| M3 | **Role-Reversal Rate** | Fraction of shared predicates where agent and patient are swapped. | **0.00** | **<= 0.02** |
| M4 | **Invented-Entity Rate** | Fraction of entities introduced in reply not grounded in user text or approved plan. | **0.00** | **<= 0.05** |
| M5 | **Superseded-Reuse Rate** | Fraction of claims restating assertions superseded by an epistemic correction. | **0.00** | **<= 0.02** |
| M6 | **Hedge-Survival Rate** | Proportion of hedged commitments preserved with epistemic hedges in reply. | **>= 0.95** | **>= 0.85** |
| M7 | **Fallback-Valid Rate** | Proportion of classical realizer outputs passing validation contract. | **1.00** | **1.00** |

## 2. Question-Engine and Dialogue Metrics
| ID | Metric Name | Definition | Target Threshold | Hard Floor |
|---|---|---|---|---|
| M9 | **Presupposition-Violation Rate** | Proportion of generated questions taking for granted unasserted facts. | **0.00** | **0.00** |
| M10 | **Gap Precision & Recall** | Precision and recall of detected structural discourse gaps vs gold gaps. | **P >= 0.85, R >= 0.80** | **P >= 0.75, R >= 0.70** |
| M11 | **Restatement Ratio** | Share of reply tokens copied directly from user spans. | **<= 0.25** | **<= 0.35** |
| M12 | **Over-Asking Rate** | Rate of asking/clarifying questions when gold move is acknowledge or hold. | **0.00** | **<= 0.10** |
| M13 | **Repeat-Question Rate** | Rate of repeating questions or question stems within a conversation window. | **0.00** | **0.00** |
| M14 | **Uptake Rate** | Rate at which user's next turn fills the targeted structural gap. | **>= 0.75** | **>= 0.65** |

## 3. Human Evaluation Dimensions (Blinded, Pairwise)
| ID | Dimension | Scale | Target Threshold |
|---|---|---|---|
| M8a | **Felt-Understood** | 1 to 5 Likert | **>= 4.0** |
| M8b | **Comfort** | 1 to 5 Likert | **>= 4.0** |
| M8c | **Invented-Detail Count** | Raw count per turn | **<= 0.05** |
| M15a | **Felt-Forced** | 1 to 5 Likert (1 is best) | **<= 1.5** |
| M15b | **Helped-Me-Think** | 1 to 5 Likert | **>= 4.0** |
| M15c | **Question-Was-Leading** | 1 to 5 Likert (1 is best) | **<= 1.2** |

## Invariant Rule
If Condition C3 (discourse question selection + uptake backoff) does not outperform Condition C0 (raw prompt) and C1 (prompt with plan) on presupposition violations and restatement ratio, the evaluation report must state this finding transparently.
