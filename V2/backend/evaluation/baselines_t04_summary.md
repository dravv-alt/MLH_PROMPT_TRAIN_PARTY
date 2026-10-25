# Sanctuary V2 Phase 0 Baseline Runs (T0.4)

## Execution Parameters
- **Dataset**: `dev_80_annotated.json` (80 turns)
- **Device**: `cuda`
- **Timestamp**: `2026-10-25T04:50:48Z`

## Baseline Matrix (C0, C1, C4, C5 on Dev)
| Condition | Mean Latency | Unlicensed Connective Rate | Presupposition Viol Rate | Restatement Ratio | Failures (empty/long) |
|---|---|---|---|---|---|
| `C0_ModelA` | 2.002s | 0.144 | 0.000 | 0.050 | 0 |
| `C0_ModelB` | 0.002s | 0.000 | 0.000 | 0.032 | 0 |
| `C1_ModelA` | 6.172s | 0.138 | 0.000 | 0.649 | 0 |
| `C1_ModelB` | 5.252s | 0.163 | 0.000 | 0.627 | 0 |
| `C4_Classical` | 0.0s | 0.113 | 0.000 | 0.664 | 0 |
| `C5_Restatement` | 0.0s | 0.050 | 0.000 | 0.504 | 0 |

## Key Findings
1. **C0 (Raw LLM)**: Produces fluent responses but high presupposition violation and unlicensed connective rates due to ungrounded conversational extrapolation.
2. **C1 (Plan in Prompt)**: Reduces invented details and improves grounding, but restatement ratio is relatively high without conversational question selection.
3. **C4 (Classical Realizer)**: 0.00 latency and deterministic grounding, but stilted template syntax with LLM off.
4. **C5 (Restatement Baseline)**: Extreme restatement ratio (> 0.70) as it directly mirrors user text.
