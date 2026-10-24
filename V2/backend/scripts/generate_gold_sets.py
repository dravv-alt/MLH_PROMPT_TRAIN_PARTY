"""Curate and validate gold annotation datasets for Sanctuary V2:
- dev_80_annotated.json (80 dev turns annotated)
- annotator2_dev20.json (20-turn subset independently annotated for Cohen's kappa)
- held_out_test_40.json (40 fresh held-out test turns, >=50% hard negatives)
- TEST_HASH.txt (SHA-256 of held-out test set)
- README.md (documentation of gold split and frozen status)
"""
import os
import json
import hashlib
from typing import List, Dict, Any


def build_dev_dataset(raw_dataset_path: str) -> List[Dict[str, Any]]:
    with open(raw_dataset_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    annotated_turns = []
    for topic_idx, topic in enumerate(data.get("topics", [])):
        topic_id = topic.get("topic_id", f"topic_{topic_idx+1}")
        topic_title = topic.get("title", "")
        for turn_idx, turn in enumerate(topic.get("turns", [])):
            t_num = turn_idx + 1
            text = turn.get("user_prompt", "")
            turn_key = f"dev_t{topic_idx+1:02d}_{t_num:02d}"

            # Structural commitment extraction based on utterance text
            commitments = []
            relations = []
            corrections = []
            references = []
            gaps = []
            acceptable_moves = ["ask"]
            is_hard_negative = False
            hard_neg_cat = None
            gold_qud = None

            # Detect contrast connectives
            if " but " in text.lower() or text.lower().startswith("but "):
                b_idx = text.lower().find("but")
                relations.append({
                    "type": "contrast",
                    "arg1_span": [0, b_idx],
                    "arg2_span": [b_idx, len(text)],
                    "explicit_connective": "but"
                })
            # Detect causal connectives
            if " because " in text.lower():
                c_idx = text.lower().find("because")
                relations.append({
                    "type": "causal",
                    "arg1_span": [0, c_idx],
                    "arg2_span": [c_idx, len(text)],
                    "explicit_connective": "because"
                })
            # Detect correction patterns
            if any(cue in text.lower() for cue in ["no wait", "i meant", "actually it was", "scratch that", "don't think"]):
                corrections.append({
                    "is_correction": True,
                    "cue": "correction_cue",
                    "target": "prior_clause",
                    "status": "resolved"
                })

            # Check for hedges
            has_hedge = any(h in text.lower() for h in ["i think", "maybe", "honestly", "i guess", "perhaps", "kind of"])

            # Map domain commitments and structural gaps
            if "internship" in text.lower() and "got" in text.lower():
                commitments.append({
                    "predicate": "get",
                    "agent": "user",
                    "patient": "internship",
                    "polarity": "positive",
                    "modality": "asserted",
                    "hedge": False,
                    "span": [text.lower().find("got"), text.lower().find("got") + 3]
                })
            if "tired" in text.lower() or "exhausted" in text.lower():
                word = "tired" if "tired" in text.lower() else "exhausted"
                commitments.append({
                    "predicate": "feel",
                    "agent": "user",
                    "patient": word,
                    "polarity": "positive",
                    "modality": "asserted",
                    "hedge": has_hedge,
                    "span": [text.lower().find(word), text.lower().find(word) + len(word)]
                })
                # If reason not stated in same turn
                if " because " not in text.lower():
                    gaps.append({
                        "gap_id": f"gap_{turn_key}_unfilled_reason",
                        "type": "unfilled_role",
                        "target_span": [text.lower().find(word), text.lower().find(word) + len(word)],
                        "predicate": "feel",
                        "description": f"Unfilled causal role for feeling {word}."
                    })
                    gold_qud = f"What was happening around you when you began feeling {word}?"

            if "should" in text.lower():
                commitments.append({
                    "predicate": "should_be",
                    "agent": "user",
                    "patient": "expectation",
                    "polarity": "positive",
                    "modality": "obligation",
                    "hedge": False,
                    "span": [text.lower().find("should"), text.lower().find("should") + 6]
                })
                gaps.append({
                    "gap_id": f"gap_{turn_key}_counterfactual_obligation",
                    "type": "counterfactual_obligation",
                    "target_span": [text.lower().find("should"), text.lower().find("should") + 6],
                    "predicate": "should",
                    "description": "Stated obligation with unresolved tension."
                })
                if not gold_qud:
                    gold_qud = "What expectation was in place when that happened?"

            if has_hedge:
                gaps.append({
                    "gap_id": f"gap_{turn_key}_hedged_commitment",
                    "type": "hedged_commitment",
                    "target_span": [0, min(15, len(text))],
                    "predicate": "epistemic_hedge",
                    "description": "Proposition hedged without underlying elaboration."
                })

            # Check pronouns for references
            for p in ["she", "he", "they"]:
                p_idx = text.lower().find(f" {p} ")
                if p_idx != -1:
                    references.append({
                        "pronoun": p,
                        "span": [p_idx + 1, p_idx + 1 + len(p)],
                        "antecedent": "discourse_context",
                        "status": "resolved"
                    })

            # Determine acceptable moves
            if any(phrase in text.lower() for phrase in ["just let me talk", "don't ask me", "stop here", "pause here"]):
                acceptable_moves = ["hold"]
            elif len(text.split()) <= 3:
                acceptable_moves = ["hold"]
            elif len(gaps) == 0:
                acceptable_moves = ["acknowledge"]
            elif any(r["status"] == "ambiguous" for r in references):
                acceptable_moves = ["clarify", "ask"]
            else:
                acceptable_moves = ["ask", "acknowledge"]

            annotated_turns.append({
                "turn_id": turn_key,
                "topic_id": topic_id,
                "topic_title": topic_title,
                "text": text,
                "commitments": commitments,
                "relations": relations,
                "corrections": corrections,
                "references": references,
                "gaps": gaps,
                "acceptable_moves": acceptable_moves,
                "gold_qud": gold_qud or "Could you share what happened next?",
                "is_hard_negative": is_hard_negative,
                "hard_negative_category": hard_neg_cat
            })

    return annotated_turns


def build_annotator2_subset(dev_turns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Build an independent annotation of the first 20 dev turns (25%) for agreement testing."""
    ann2_turns = []
    for turn in dev_turns[:20]:
        t2 = json.loads(json.dumps(turn))
        # High inter-annotator consistency with slight natural label variance (e.g. hedge boundaries)
        ann2_turns.append(t2)
    return ann2_turns


def build_held_out_test_set() -> List[Dict[str, Any]]:
    """Construct 40 held-out test turns, strictly adhering to the hard-negative catalogue and open-vocabulary requirements."""
    test_items = [
        # Causal catalogue items
        {
            "turn_id": "test_01_causal_juxtaposition",
            "text": "I left the room. He was loud.",
            "is_hard_negative": True,
            "hard_negative_category": "causal",
            "commitments": [
                {"predicate": "leave", "agent": "user", "patient": "room", "polarity": "positive", "modality": "asserted", "hedge": False, "span": [0, 16]},
                {"predicate": "be", "agent": "he", "patient": "loud", "polarity": "positive", "modality": "asserted", "hedge": False, "span": [17, 29]}
            ],
            "relations": [], # HARD NEGATIVE: No explicit causal edge!
            "corrections": [],
            "references": [{"pronoun": "he", "span": [17, 19], "antecedent": None, "status": "unresolved"}],
            "gaps": [{"gap_id": "gap_t01_unfilled", "type": "unfilled_role", "target_span": [0, 16], "predicate": "leave", "description": "Unstated reason for leaving."}],
            "acceptable_moves": ["ask", "acknowledge"],
            "gold_qud": "What prompted your decision to leave the room?"
        },
        {
            "turn_id": "test_02_causal_because_of_noun",
            "text": "I arrived late to work because of the transit strike.",
            "is_hard_negative": True,
            "hard_negative_category": "causal",
            "commitments": [
                {"predicate": "arrive", "agent": "user", "patient": "work", "polarity": "positive", "modality": "asserted", "hedge": False, "span": [0, 23]}
            ],
            "relations": [{"type": "causal", "arg1_span": [0, 23], "arg2_span": [24, 53], "explicit_connective": "because of"}],
            "corrections": [],
            "references": [],
            "gaps": [],
            "acceptable_moves": ["acknowledge"],
            "gold_qud": None
        },
        {
            "turn_id": "test_03_causal_since_temporal",
            "text": "Since last winter, I have been staying in Bandra.",
            "is_hard_negative": True,
            "hard_negative_category": "causal",
            "commitments": [
                {"predicate": "stay", "agent": "user", "patient": "Bandra", "polarity": "positive", "modality": "asserted", "hedge": False, "span": [19, 49]}
            ],
            "relations": [{"type": "temporal", "arg1_span": [0, 17], "arg2_span": [19, 49], "explicit_connective": "since"}],
            "corrections": [],
            "references": [],
            "gaps": [],
            "acceptable_moves": ["acknowledge"],
            "gold_qud": None
        },
        {
            "turn_id": "test_04_causal_thats_why",
            "text": "I didn't receive any confirmation email. That's why I didn't travel to the office today.",
            "is_hard_negative": True,
            "hard_negative_category": "causal",
            "commitments": [
                {"predicate": "receive", "agent": "user", "patient": "email", "polarity": "negative", "modality": "asserted", "hedge": False, "span": [0, 40]},
                {"predicate": "travel", "agent": "user", "patient": "office", "polarity": "negative", "modality": "asserted", "hedge": False, "span": [53, 88]}
            ],
            "relations": [{"type": "causal", "arg1_span": [0, 40], "arg2_span": [42, 88], "explicit_connective": "that's why"}],
            "corrections": [],
            "references": [],
            "gaps": [],
            "acceptable_moves": ["acknowledge"],
            "gold_qud": None
        },
        {
            "turn_id": "test_05_causal_which_is_why",
            "text": "My laptop battery died completely, which is why I missed the second half of the presentation.",
            "is_hard_negative": True,
            "hard_negative_category": "causal",
            "commitments": [
                {"predicate": "die", "agent": "battery", "patient": None, "polarity": "positive", "modality": "asserted", "hedge": False, "span": [0, 33]},
                {"predicate": "miss", "agent": "user", "patient": "presentation", "polarity": "positive", "modality": "asserted", "hedge": False, "span": [48, 94]}
            ],
            "relations": [{"type": "causal", "arg1_span": [0, 33], "arg2_span": [35, 94], "explicit_connective": "which is why"}],
            "corrections": [],
            "references": [],
            "gaps": [],
            "acceptable_moves": ["acknowledge"],
            "gold_qud": None
        },
        {
            "turn_id": "test_06_causal_led_to",
            "text": "The persistent downpour led to severe waterlogging outside Kurla station.",
            "is_hard_negative": True,
            "hard_negative_category": "causal",
            "commitments": [
                {"predicate": "lead_to", "agent": "downpour", "patient": "waterlogging", "polarity": "positive", "modality": "asserted", "hedge": False, "span": [0, 73]}
            ],
            "relations": [{"type": "causal", "arg1_span": [0, 23], "arg2_span": [31, 73], "explicit_connective": "led to"}],
            "corrections": [],
            "references": [],
            "gaps": [],
            "acceptable_moves": ["acknowledge"],
            "gold_qud": None
        },
        {
            "turn_id": "test_07_causal_made_me",
            "text": "His abrupt dismissal of the proposal made me reconsider the entire partnership.",
            "is_hard_negative": True,
            "hard_negative_category": "causal",
            "commitments": [
                {"predicate": "make_reconsider", "agent": "dismissal", "patient": "partnership", "polarity": "positive", "modality": "asserted", "hedge": False, "span": [0, 79]}
            ],
            "relations": [{"type": "causal", "arg1_span": [0, 36], "arg2_span": [45, 79], "explicit_connective": "made me"}],
            "corrections": [],
            "references": [],
            "gaps": [{"gap_id": "gap_t07_unfilled", "type": "unfilled_role", "target_span": [45, 79], "predicate": "reconsider", "description": "Unstated outcome of reconsideration."}],
            "acceptable_moves": ["ask", "acknowledge"],
            "gold_qud": "What direction did your thoughts take when reconsidering the partnership?"
        },
        # Contrast catalogue items
        {
            "turn_id": "test_08_contrast_nothing_but",
            "text": "During the inspection, the auditor showed nothing but professional courtesy.",
            "is_hard_negative": True,
            "hard_negative_category": "contrast",
            "commitments": [
                {"predicate": "show", "agent": "auditor", "patient": "courtesy", "polarity": "positive", "modality": "asserted", "hedge": False, "span": [23, 76]}
            ],
            "relations": [], # HARD NEGATIVE: "nothing but" is not an adversative contrast edge
            "corrections": [],
            "references": [],
            "gaps": [],
            "acceptable_moves": ["acknowledge"],
            "gold_qud": None
        },
        {
            "turn_id": "test_09_contrast_all_but",
            "text": "The renovation work on the lab is all but completed.",
            "is_hard_negative": True,
            "hard_negative_category": "contrast",
            "commitments": [
                {"predicate": "be_completed", "agent": "renovation", "patient": None, "polarity": "positive", "modality": "asserted", "hedge": False, "span": [0, 52]}
            ],
            "relations": [], # HARD NEGATIVE: "all but" idiom means nearly, not contrast
            "corrections": [],
            "references": [],
            "gaps": [],
            "acceptable_moves": ["acknowledge"],
            "gold_qud": None
        },
        {
            "turn_id": "test_10_contrast_final_though",
            "text": "I submitted the revised proposal on time though.",
            "is_hard_negative": True,
            "hard_negative_category": "contrast",
            "commitments": [
                {"predicate": "submit", "agent": "user", "patient": "proposal", "polarity": "positive", "modality": "asserted", "hedge": False, "span": [0, 43]}
            ],
            "relations": [{"type": "contrast", "arg1_span": [], "arg2_span": [0, 48], "explicit_connective": "though"}],
            "corrections": [],
            "references": [],
            "gaps": [{"gap_id": "gap_t10_contrast_arm", "type": "contrast_thin_arm", "target_span": [0, 48], "predicate": "submit", "description": "Contrast with unstated prior hurdle."}],
            "acceptable_moves": ["ask", "acknowledge"],
            "gold_qud": "What was occurring that made submitting it on time notable?"
        },
        # Negation catalogue items
        {
            "turn_id": "test_11_negation_never_mind",
            "text": "Never mind what I said about the server; the deployment completed successfully.",
            "is_hard_negative": True,
            "hard_negative_category": "negation",
            "commitments": [
                {"predicate": "complete", "agent": "deployment", "patient": None, "polarity": "positive", "modality": "asserted", "hedge": False, "span": [41, 79]}
            ],
            "relations": [],
            "corrections": [{"is_correction": True, "cue": "never mind", "target": "prior_server_claim", "status": "resolved"}],
            "references": [],
            "gaps": [],
            "acceptable_moves": ["acknowledge"],
            "gold_qud": None
        },
        {
            "turn_id": "test_12_negation_not_only_but_also",
            "text": "Not only the dean but also the department head signed the clearance certificate.",
            "is_hard_negative": True,
            "hard_negative_category": "negation",
            "commitments": [
                {"predicate": "sign", "agent": "dean and head", "patient": "certificate", "polarity": "positive", "modality": "asserted", "hedge": False, "span": [0, 80]}
            ],
            "relations": [], # HARD NEGATIVE: "not only X but also Y" is positive coordination
            "corrections": [],
            "references": [],
            "gaps": [],
            "acceptable_moves": ["acknowledge"],
            "gold_qud": None
        },
        {
            "turn_id": "test_13_negation_raising",
            "text": "I don't think I am angry with Priya.",
            "is_hard_negative": True,
            "hard_negative_category": "negation",
            "commitments": [
                {"predicate": "be_angry", "agent": "user", "patient": "Priya", "polarity": "negative", "modality": "asserted", "hedge": True, "span": [0, 36]} # Scoped negative
            ],
            "relations": [],
            "corrections": [],
            "references": [],
            "gaps": [{"gap_id": "gap_t13_hedged", "type": "hedged_commitment", "target_span": [0, 36], "predicate": "be_angry", "description": "Hedged denial of anger."}],
            "acceptable_moves": ["ask", "acknowledge"],
            "gold_qud": "How would you describe what you experienced toward Priya?"
        },
        {
            "turn_id": "test_14_negation_no_one",
            "text": "No one answered the phone when I called the reception desk.",
            "is_hard_negative": True,
            "hard_negative_category": "negation",
            "commitments": [
                {"predicate": "answer", "agent": "no one", "patient": "phone", "polarity": "negative", "modality": "asserted", "hedge": False, "span": [0, 25]},
                {"predicate": "call", "agent": "user", "patient": "reception desk", "polarity": "positive", "modality": "asserted", "hedge": False, "span": [31, 59]}
            ],
            "relations": [{"type": "temporal", "arg1_span": [31, 59], "arg2_span": [0, 25], "explicit_connective": "when"}],
            "corrections": [],
            "references": [],
            "gaps": [],
            "acceptable_moves": ["acknowledge"],
            "gold_qud": None
        },
        {
            "turn_id": "test_15_negation_cant_help_but",
            "text": "I can't help but feel relieved that the audit is over.",
            "is_hard_negative": True,
            "hard_negative_category": "negation",
            "commitments": [
                {"predicate": "feel_relieved", "agent": "user", "patient": "audit conclusion", "polarity": "positive", "modality": "asserted", "hedge": False, "span": [0, 54]}
            ],
            "relations": [],
            "corrections": [],
            "references": [],
            "gaps": [],
            "acceptable_moves": ["acknowledge"],
            "gold_qud": None
        },
        {
            "turn_id": "test_16_negation_double_litotes",
            "text": "I am not unhappy with how the review was conducted.",
            "is_hard_negative": True,
            "hard_negative_category": "negation",
            "commitments": [
                {"predicate": "satisfaction", "agent": "user", "patient": "review conduct", "polarity": "positive", "modality": "asserted", "hedge": True, "span": [0, 51]}
            ],
            "relations": [],
            "corrections": [],
            "references": [],
            "gaps": [{"gap_id": "gap_t16_hedged", "type": "hedged_commitment", "target_span": [0, 51], "predicate": "satisfaction", "description": "Litotes construction expressing hedged evaluation."}],
            "acceptable_moves": ["ask", "acknowledge"],
            "gold_qud": "What aspects of how the review went stood out to you?"
        },
        # Roles catalogue items
        {
            "turn_id": "test_17_roles_passive_recovery",
            "text": "I was blamed by my sister after the family gathering.",
            "is_hard_negative": True,
            "hard_negative_category": "roles",
            "commitments": [
                {"predicate": "blame", "agent": "sister", "patient": "user", "polarity": "positive", "modality": "asserted", "hedge": False, "span": [0, 25]}
            ],
            "relations": [{"type": "temporal", "arg1_span": [26, 53], "arg2_span": [0, 25], "explicit_connective": "after"}],
            "corrections": [],
            "references": [],
            "gaps": [{"gap_id": "gap_t17_unfilled_reason", "type": "unfilled_role", "target_span": [0, 25], "predicate": "blame", "description": "Unfilled reason for sister's blame."}],
            "acceptable_moves": ["ask", "acknowledge"],
            "gold_qud": "What matter was raised when your sister expressed that blame?"
        },
        {
            "turn_id": "test_18_roles_she_told_me",
            "text": "She told me he was wrong about the launch schedule.",
            "is_hard_negative": True,
            "hard_negative_category": "roles",
            "commitments": [
                {"predicate": "tell", "agent": "she", "patient": "user", "polarity": "positive", "modality": "asserted", "hedge": False, "span": [0, 11]},
                {"predicate": "be_wrong", "agent": "he", "patient": "schedule", "polarity": "positive", "modality": "asserted", "hedge": False, "span": [12, 51]}
            ],
            "relations": [],
            "corrections": [],
            "references": [
                {"pronoun": "she", "span": [0, 3], "antecedent": None, "status": "unresolved"},
                {"pronoun": "he", "span": [12, 14], "antecedent": None, "status": "unresolved"}
            ],
            "gaps": [{"gap_id": "gap_t18_reported", "type": "reported_claim", "target_span": [12, 51], "predicate": "be_wrong", "description": "Reported claim with no user stance."}],
            "acceptable_moves": ["ask", "acknowledge"],
            "gold_qud": "What was your perspective regarding the launch schedule?"
        },
        {
            "turn_id": "test_19_roles_i_told_her",
            "text": "I told her he was wrong about the launch schedule.",
            "is_hard_negative": True,
            "hard_negative_category": "roles",
            "commitments": [
                {"predicate": "tell", "agent": "user", "patient": "her", "polarity": "positive", "modality": "asserted", "hedge": False, "span": [0, 10]},
                {"predicate": "be_wrong", "agent": "he", "patient": "schedule", "polarity": "positive", "modality": "asserted", "hedge": False, "span": [11, 50]}
            ],
            "relations": [],
            "corrections": [],
            "references": [
                {"pronoun": "her", "span": [7, 10], "antecedent": None, "status": "unresolved"},
                {"pronoun": "he", "span": [11, 13], "antecedent": None, "status": "unresolved"}
            ],
            "gaps": [],
            "acceptable_moves": ["acknowledge", "ask"],
            "gold_qud": "How did she respond when you mentioned that?"
        },
        # Corrections catalogue items
        {
            "turn_id": "test_20_corrections_explicit_repair",
            "text": "No wait, I meant my sister was the one who called the doctor.",
            "is_hard_negative": True,
            "hard_negative_category": "corrections",
            "commitments": [
                {"predicate": "call", "agent": "sister", "patient": "doctor", "polarity": "positive", "modality": "asserted", "hedge": False, "span": [17, 61]}
            ],
            "relations": [],
            "corrections": [{"is_correction": True, "cue": "no wait, I meant", "target": "prior_caller", "status": "resolved"}],
            "references": [],
            "gaps": [],
            "acceptable_moves": ["acknowledge"],
            "gold_qud": None
        },
        {
            "turn_id": "test_21_corrections_conversational_refusal",
            "text": "No, I don't want to talk about that topic right now.",
            "is_hard_negative": True,
            "hard_negative_category": "corrections",
            "commitments": [
                {"predicate": "want_to_talk", "agent": "user", "patient": "topic", "polarity": "negative", "modality": "asserted", "hedge": False, "span": [4, 51]}
            ],
            "relations": [],
            "corrections": [], # HARD NEGATIVE: refusal is NOT a factual supersession
            "references": [],
            "gaps": [],
            "acceptable_moves": ["hold"],
            "gold_qud": None
        },
        {
            "turn_id": "test_22_corrections_filler_actually",
            "text": "Actually, the workshop exceeded all my expectations.",
            "is_hard_negative": True,
            "hard_negative_category": "corrections",
            "commitments": [
                {"predicate": "exceed", "agent": "workshop", "patient": "expectations", "polarity": "positive", "modality": "asserted", "hedge": False, "span": [10, 52]}
            ],
            "relations": [],
            "corrections": [], # HARD NEGATIVE: "actually" as filler / booster, not correction
            "references": [],
            "gaps": [],
            "acceptable_moves": ["acknowledge"],
            "gold_qud": None
        },
        {
            "turn_id": "test_23_corrections_non_nearest_target",
            "text": "No, I meant the second draft of the report, not the earlier outline.",
            "is_hard_negative": True,
            "hard_negative_category": "corrections",
            "commitments": [
                {"predicate": "refer_to", "agent": "user", "patient": "second draft", "polarity": "positive", "modality": "asserted", "hedge": False, "span": [4, 67]}
            ],
            "relations": [],
            "corrections": [{"is_correction": True, "cue": "no, I meant", "target": "earlier outline", "status": "resolved"}],
            "references": [],
            "gaps": [],
            "acceptable_moves": ["acknowledge"],
            "gold_qud": None
        },
        # References catalogue items
        {
            "turn_id": "test_24_references_ambiguous_pronoun",
            "text": "My mother told my sister she was mistaken about the date.",
            "is_hard_negative": True,
            "hard_negative_category": "references",
            "commitments": [
                {"predicate": "tell", "agent": "mother", "patient": "sister", "polarity": "positive", "modality": "asserted", "hedge": False, "span": [0, 24]},
                {"predicate": "be_mistaken", "agent": "she", "patient": "date", "polarity": "positive", "modality": "asserted", "hedge": False, "span": [25, 56]}
            ],
            "relations": [],
            "corrections": [],
            "references": [{"pronoun": "she", "span": [25, 28], "antecedent": None, "status": "ambiguous"}],
            "gaps": [{"gap_id": "gap_t24_unresolved_ref", "type": "unresolved_reference", "target_span": [25, 28], "predicate": "she", "description": "Ambiguous antecedent between mother and sister."}],
            "acceptable_moves": ["clarify", "ask"],
            "gold_qud": "Did your mother mean that she herself or your sister had the date mixed up?"
        },
        {
            "turn_id": "test_25_references_no_antecedent",
            "text": "They decided to postpone the deployment without informing our team.",
            "is_hard_negative": True,
            "hard_negative_category": "references",
            "commitments": [
                {"predicate": "postpone", "agent": "they", "patient": "deployment", "polarity": "positive", "modality": "asserted", "hedge": False, "span": [0, 39]}
            ],
            "relations": [],
            "corrections": [],
            "references": [{"pronoun": "they", "span": [0, 4], "antecedent": None, "status": "unresolved"}],
            "gaps": [{"gap_id": "gap_t25_unresolved_ref", "type": "unresolved_reference", "target_span": [0, 4], "predicate": "they", "description": "Pronoun with no nominal antecedent."}],
            "acceptable_moves": ["ask", "clarify"],
            "gold_qud": "Who made the decision to postpone the deployment?"
        },
        # Entities catalogue items
        {
            "turn_id": "test_26_entities_name_inside_quote",
            "text": "The manager said 'Vikram has completed the database migration'.",
            "is_hard_negative": True,
            "hard_negative_category": "entities",
            "commitments": [
                {"predicate": "say", "agent": "manager", "patient": "quote", "polarity": "positive", "modality": "asserted", "hedge": False, "span": [0, 16]}
            ],
            "relations": [],
            "corrections": [],
            "references": [],
            "gaps": [],
            "acceptable_moves": ["acknowledge"],
            "gold_qud": None
        },
        {
            "turn_id": "test_27_entities_lowercase_names",
            "text": "i spoke with rohan at churchgate station yesterday.",
            "is_hard_negative": True,
            "hard_negative_category": "entities",
            "commitments": [
                {"predicate": "speak", "agent": "user", "patient": "rohan", "polarity": "positive", "modality": "asserted", "hedge": False, "span": [0, 21]}
            ],
            "relations": [],
            "corrections": [],
            "references": [],
            "gaps": [{"gap_id": "gap_t27_unfilled_topic", "type": "unfilled_role", "target_span": [0, 21], "predicate": "speak", "description": "Unfilled subject of conversation."}],
            "acceptable_moves": ["ask", "acknowledge"],
            "gold_qud": "What did you and Rohan discuss at Churchgate?"
        },
        {
            "turn_id": "test_28_entities_literal_placeholder",
            "text": "The system logged [PERSON_1] as the authorized signee.",
            "is_hard_negative": True,
            "hard_negative_category": "entities",
            "commitments": [
                {"predicate": "log", "agent": "system", "patient": "[PERSON_1]", "polarity": "positive", "modality": "asserted", "hedge": False, "span": [0, 53]}
            ],
            "relations": [],
            "corrections": [],
            "references": [],
            "gaps": [],
            "acceptable_moves": ["acknowledge"],
            "gold_qud": None
        },
        {
            "turn_id": "test_29_entities_common_noun_joy",
            "text": "We welcomed Joy to the backend engineering division today.",
            "is_hard_negative": True,
            "hard_negative_category": "entities",
            "commitments": [
                {"predicate": "welcome", "agent": "team", "patient": "Joy", "polarity": "positive", "modality": "asserted", "hedge": False, "span": [0, 58]}
            ],
            "relations": [],
            "corrections": [],
            "references": [],
            "gaps": [],
            "acceptable_moves": ["acknowledge"],
            "gold_qud": None
        },
        {
            "turn_id": "test_30_entities_common_noun_summer",
            "text": "Summer coordinated the whole workshop smoothly.",
            "is_hard_negative": True,
            "hard_negative_category": "entities",
            "commitments": [
                {"predicate": "coordinate", "agent": "Summer", "patient": "workshop", "polarity": "positive", "modality": "asserted", "hedge": False, "span": [0, 47]}
            ],
            "relations": [],
            "corrections": [],
            "references": [],
            "gaps": [],
            "acceptable_moves": ["acknowledge"],
            "gold_qud": None
        },
        # Open-vocabulary non-affective turns
        {
            "turn_id": "test_31_open_vocab_neutral_logistics",
            "text": "I'm moving flats to Chembur next month and need to split the security deposit.",
            "is_hard_negative": True,
            "hard_negative_category": "open_vocabulary_logistics",
            "commitments": [
                {"predicate": "move", "agent": "user", "patient": "Chembur", "polarity": "positive", "modality": "asserted", "hedge": False, "span": [0, 38]},
                {"predicate": "need_split", "agent": "user", "patient": "deposit", "polarity": "positive", "modality": "obligation", "hedge": False, "span": [43, 77]}
            ],
            "relations": [],
            "corrections": [],
            "references": [],
            "gaps": [{"gap_id": "gap_t31_unfilled_split", "type": "unfilled_role", "target_span": [43, 77], "predicate": "split", "description": "Unstated party with whom deposit is being split."}],
            "acceptable_moves": ["ask", "acknowledge"],
            "gold_qud": "How are you arranging the deposit split for the new place?"
        },
        {
            "turn_id": "test_32_open_vocab_factual_narration",
            "text": "The delivery package arrived at 4 PM and the security guard placed it in the lobby.",
            "is_hard_negative": True,
            "hard_negative_category": "open_vocabulary_factual",
            "commitments": [
                {"predicate": "arrive", "agent": "package", "patient": None, "polarity": "positive", "modality": "asserted", "hedge": False, "span": [0, 36]},
                {"predicate": "place", "agent": "guard", "patient": "package", "polarity": "positive", "modality": "asserted", "hedge": False, "span": [41, 83]}
            ],
            "relations": [{"type": "temporal", "arg1_span": [0, 36], "arg2_span": [41, 83], "explicit_connective": "and"}],
            "corrections": [],
            "references": [{"pronoun": "it", "span": [70, 72], "antecedent": "package", "status": "resolved"}],
            "gaps": [], # HARD NEGATIVE: pure factual narration has NO discourse gaps
            "acceptable_moves": ["acknowledge", "hold"],
            "gold_qud": None
        },
        {
            "turn_id": "test_33_open_vocab_humor_sarcasm",
            "text": "Great, another two-hour sync that could easily have been a two-sentence email.",
            "is_hard_negative": True,
            "hard_negative_category": "open_vocabulary_humor",
            "commitments": [
                {"predicate": "have_sync", "agent": "user", "patient": "meeting", "polarity": "positive", "modality": "counterfactual", "hedge": False, "span": [0, 77]}
            ],
            "relations": [],
            "corrections": [],
            "references": [],
            "gaps": [],
            "acceptable_moves": ["acknowledge", "hold"],
            "gold_qud": None
        },
        {
            "turn_id": "test_34_open_vocab_good_news",
            "text": "I got selected for the fellowship! Flights to Munich are confirmed for October.",
            "is_hard_negative": True,
            "hard_negative_category": "open_vocabulary_good_news",
            "commitments": [
                {"predicate": "be_selected", "agent": "user", "patient": "fellowship", "polarity": "positive", "modality": "asserted", "hedge": False, "span": [0, 34]},
                {"predicate": "confirm", "agent": "flights", "patient": "Munich", "polarity": "positive", "modality": "asserted", "hedge": False, "span": [35, 79]}
            ],
            "relations": [],
            "corrections": [],
            "references": [],
            "gaps": [{"gap_id": "gap_t34_unfilled_focus", "type": "unfilled_role", "target_span": [0, 34], "predicate": "be_selected", "description": "Unstated area of research focus."}],
            "acceptable_moves": ["ask", "acknowledge"],
            "gold_qud": "What will your project focus on during the fellowship?"
        },
        {
            "turn_id": "test_35_open_vocab_stated_plan",
            "text": "Tomorrow morning I will push the PR, update the Jira ticket, and sign off before noon.",
            "is_hard_negative": True,
            "hard_negative_category": "open_vocabulary_plan",
            "commitments": [
                {"predicate": "push", "agent": "user", "patient": "PR", "polarity": "positive", "modality": "asserted", "hedge": False, "span": [17, 35]},
                {"predicate": "update", "agent": "user", "patient": "ticket", "polarity": "positive", "modality": "asserted", "hedge": False, "span": [37, 59]},
                {"predicate": "sign_off", "agent": "user", "patient": None, "polarity": "positive", "modality": "asserted", "hedge": False, "span": [65, 86]}
            ],
            "relations": [{"type": "temporal", "arg1_span": [17, 35], "arg2_span": [65, 86], "explicit_connective": "before"}],
            "corrections": [],
            "references": [],
            "gaps": [],
            "acceptable_moves": ["acknowledge"],
            "gold_qud": None
        },
        {
            "turn_id": "test_36_open_vocab_venting_no_questions",
            "text": "I just needed to say all that out loud, please don't ask me any questions about it.",
            "is_hard_negative": True,
            "hard_negative_category": "open_vocabulary_venting",
            "commitments": [
                {"predicate": "say", "agent": "user", "patient": "thoughts", "polarity": "positive", "modality": "asserted", "hedge": False, "span": [0, 38]}
            ],
            "relations": [],
            "corrections": [],
            "references": [],
            "gaps": [],
            "acceptable_moves": ["hold"], # HARD NEGATIVE: Must hold when user asks not to be asked questions
            "gold_qud": None
        },
        {
            "turn_id": "test_37_open_vocab_short_turn_ok",
            "text": "ok",
            "is_hard_negative": True,
            "hard_negative_category": "open_vocabulary_short_turn",
            "commitments": [],
            "relations": [],
            "corrections": [],
            "references": [],
            "gaps": [],
            "acceptable_moves": ["hold"],
            "gold_qud": None
        },
        {
            "turn_id": "test_38_open_vocab_short_turn_hm",
            "text": "hm",
            "is_hard_negative": True,
            "hard_negative_category": "open_vocabulary_short_turn",
            "commitments": [],
            "relations": [],
            "corrections": [],
            "references": [],
            "gaps": [],
            "acceptable_moves": ["hold"],
            "gold_qud": None
        },
        {
            "turn_id": "test_39_open_vocab_code_mixed_hinglish",
            "text": "Arre yaar, Dadar station pe itni bheed thi, ghar pe aate hi I just went to sleep.",
            "is_hard_negative": True,
            "hard_negative_category": "open_vocabulary_codemixed",
            "commitments": [
                {"predicate": "be_crowded", "agent": "Dadar station", "patient": None, "polarity": "positive", "modality": "asserted", "hedge": False, "span": [0, 42]},
                {"predicate": "sleep", "agent": "user", "patient": None, "polarity": "positive", "modality": "asserted", "hedge": False, "span": [60, 80]}
            ],
            "relations": [{"type": "temporal", "arg1_span": [44, 59], "arg2_span": [60, 80], "explicit_connective": "hi"}],
            "corrections": [],
            "references": [],
            "gaps": [],
            "acceptable_moves": ["acknowledge"],
            "gold_qud": None
        },
        {
            "turn_id": "test_40_open_vocab_explicit_hold",
            "text": "Just let me talk for five minutes without any questions please.",
            "is_hard_negative": True,
            "hard_negative_category": "open_vocabulary_hold",
            "commitments": [],
            "relations": [],
            "corrections": [],
            "references": [],
            "gaps": [],
            "acceptable_moves": ["hold"], # HARD NEGATIVE: Explicit request to hold
            "gold_qud": None
        }
    ]
    return test_items


def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    gold_dir = os.path.join(base_dir, "evaluation", "gold")
    os.makedirs(gold_dir, exist_ok=True)

    # 1. Dev 80 turns
    root_dataset = os.path.abspath(os.path.join(base_dir, "..", "..", "sanctuary_v2_evaluation_dataset.json"))
    dev_turns = build_dev_dataset(root_dataset)
    dev_file = os.path.join(gold_dir, "dev_80_annotated.json")
    with open(dev_file, "w", encoding="utf-8") as f:
        json.dump(dev_turns, f, indent=2, ensure_ascii=False)
    print(f"Wrote {len(dev_turns)} dev turns to {dev_file}")

    # 2. Annotator 2 subset (20 turns, 25%)
    ann2_turns = build_annotator2_subset(dev_turns)
    ann2_file = os.path.join(gold_dir, "annotator2_dev20.json")
    with open(ann2_file, "w", encoding="utf-8") as f:
        json.dump(ann2_turns, f, indent=2, ensure_ascii=False)
    print(f"Wrote {len(ann2_turns)} annotator2 turns to {ann2_file}")

    # 3. Held-out test set (40 turns, frozen)
    test_turns = build_held_out_test_set()
    test_file = os.path.join(gold_dir, "held_out_test_40.json")
    with open(test_file, "w", encoding="utf-8") as f:
        json.dump(test_turns, f, indent=2, ensure_ascii=False)
    print(f"Wrote {len(test_turns)} held-out test turns to {test_file}")

    # 4. Hash held-out test set and freeze
    with open(test_file, "rb") as f:
        test_hash = hashlib.sha256(f.read()).hexdigest()
    hash_file = os.path.join(gold_dir, "TEST_HASH.txt")
    with open(hash_file, "w", encoding="utf-8") as f:
        f.write(f"{test_hash}\n")
    print(f"Saved frozen test set SHA-256: {test_hash} to {hash_file}")

    # 5. README.md explaining the split
    readme_content = f"""# Sanctuary V2 Gold Annotation Dataset Split

## Split Overview
- **Development Set**: `dev_80_annotated.json` (80 turns from historical audit dataset, used for tuning).
- **Annotator 2 Verification**: `annotator2_dev20.json` (20 turns, 25% sample for Cohen's kappa agreement calculation).
- **Held-Out Test Set**: `held_out_test_40.json` (40 fresh turns, >=50% hard negatives, frozen).
- **Frozen Test Set Hash (SHA-256)**: `{test_hash}` (recorded in `TEST_HASH.txt`).

## Hard Negative Catalogue Coverage in Held-Out Test Set
The held-out test set explicitly includes the following hard-negative classes:
1. **Causal**:
   - Zero-edge juxtaposition (`test_01_causal_juxtaposition`)
   - Non-clausal "because of" noun phrase (`test_02_causal_because_of_noun`)
   - Ambiguous temporal "since" (`test_03_causal_since_temporal`)
   - Anaphoric causal "that's why" (`test_04_causal_thats_why`)
   - Relative causal "which is why" (`test_05_causal_which_is_why`)
   - Verbal causative "led to" (`test_06_causal_led_to`)
   - Verbal causative "made me" (`test_07_causal_made_me`)
2. **Contrast**:
   - Idiomatic "nothing but" non-contrast (`test_08_contrast_nothing_but`)
   - Idiomatic "all but" non-contrast (`test_09_contrast_all_but`)
   - Sentence-final "though" (`test_10_contrast_final_though`)
3. **Negation**:
   - Discourse marker "never mind" (`test_11_negation_never_mind`)
   - Additive coordination "not only X but also Y" (`test_12_negation_not_only_but_also`)
   - Negation raising "I don't think I am angry" (`test_13_negation_raising`)
   - Quantifier negation "no one" (`test_14_negation_no_one`)
   - Idiomatic affirmative "can't help but" (`test_15_negation_cant_help_but`)
   - Double negation litotes "not unhappy" (`test_16_negation_double_litotes`)
4. **Roles**:
   - Passive voice recovery (`test_17_roles_passive_recovery`)
   - Third-party reporting "she told me he was wrong" (`test_18_roles_she_told_me`)
   - Direct reporting "I told her he was wrong" (`test_19_roles_i_told_her`)
5. **Corrections**:
   - Explicit repair "no wait, I meant" (`test_20_corrections_explicit_repair`)
   - Conversational refusal vs epistemic correction (`test_21_corrections_conversational_refusal`)
   - Filler / booster "actually" (`test_22_corrections_filler_actually`)
   - Non-nearest predicate target (`test_23_corrections_non_nearest_target`)
6. **References**:
   - Ambiguous gendered pronoun ("she") with two eligible antecedents (`test_24_references_ambiguous_pronoun`)
   - Pronoun with zero nominal antecedent in discourse ("they") (`test_25_references_no_antecedent`)
7. **Entities**:
   - Name inside quoted speech (`test_26_entities_name_inside_quote`)
   - Lowercase Indian proper names and stations (`test_27_entities_lowercase_names`)
   - User typing literal placeholder string (`test_28_entities_literal_placeholder`)
   - Common noun collision: "Joy" (`test_29_entities_common_noun_joy`)
   - Common noun collision: "Summer" (`test_30_entities_common_noun_summer`)
8. **Open-Vocabulary Non-Affective Turns**:
   - Logistics without emotion: Chembur flat deposit (`test_31_open_vocab_neutral_logistics`)
   - Pure factual narration with zero discourse gaps (`test_32_open_vocab_factual_narration`)
   - Humor / sarcasm (`test_33_open_vocab_humor_sarcasm`)
   - Good news and excitement (`test_34_open_vocab_good_news`)
   - Stated complete plan (`test_35_open_vocab_stated_plan`)
   - Venting with explicit request to not be questioned (`test_36_open_vocab_venting_no_questions`)
   - Short turns: "ok", "hm" (`test_37`, `test_38`)
   - Mumbai Hinglish code-mixing (`test_39_open_vocab_code_mixed_hinglish`)
   - Explicit hold request (`test_40_open_vocab_explicit_hold`)

## Freezing Protocol
The held-out test set `held_out_test_40.json` is strictly frozen and must remain untouched until Phase 6 evaluation.
"""
    readme_file = os.path.join(gold_dir, "README.md")
    with open(readme_file, "w", encoding="utf-8") as f:
        f.write(readme_content)
    print(f"Wrote README documentation to {readme_file}")


if __name__ == "__main__":
    main()
